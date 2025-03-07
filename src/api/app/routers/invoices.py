from app.lifespan_manager import get_db_connection_pool, get_storage_service, get_azure_doc_intelligence_service
from app.models import Invoice, InvoiceEdit, ListResponse, InvoiceAnalyzeResult
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from datetime import datetime
from pydantic import parse_obj_as
import json
import traceback

# Initialize the router
router = APIRouter(
    prefix = "/invoices",
    tags = ["Invoices"],
    dependencies = [Depends(get_db_connection_pool)],
    responses = {404: {"description": "Not found"}}
)

@router.get("/", response_model=ListResponse[Invoice])
async def list_invoices(vendor_id: int = -1, skip: int = 0, limit: int = 10, sortby: str = None, pool = Depends(get_db_connection_pool)):
    """Retrieves a list of invoices from the database."""
    async with pool.acquire() as conn:
        orderby = 'id'
        if (sortby):
            orderby = sortby

        if limit < 0:
            if vendor_id > 0:
                rows = await conn.fetch('SELECT * FROM invoices WHERE vendor_id = $1 ORDER BY $2;', vendor_id, orderby)
            else:
                rows = await conn.fetch('SELECT * FROM invoices ORDER BY $1;', orderby)
        else:
            if vendor_id > 0:
                rows = await conn.fetch('SELECT * FROM invoices WHERE vendor_id = $1 ORDER BY $2 LIMIT $3 OFFSET $4;', vendor_id, orderby, limit, skip)
            else:
                rows = await conn.fetch('SELECT * FROM invoices ORDER BY $1 LIMIT $2 OFFSET $3;', orderby, limit, skip)

        invoices = parse_obj_as(list[Invoice], [dict(row) for row in rows])

        if (vendor_id > 0):
            total = await conn.fetchval('SELECT COUNT(*) FROM invoices WHERE vendor_id = $1;', vendor_id)
        else:
            total = await conn.fetchval('SELECT COUNT(*) FROM invoices;')

    if (limit <= -1):
        limit = total
        
    return ListResponse(data=invoices, total = total, skip = skip, limit = limit)

   
@router.get("/{invoice_id}", response_model=Invoice)
async def get_by_id(invoice_id: int, pool = Depends(get_db_connection_pool)):
    """Retrieves an invoice by ID from the database."""
    async with pool.acquire() as conn:
        row = await conn.fetchrow('SELECT * FROM invoices WHERE id = $1;', invoice_id)
        if row is None:
            raise HTTPException(status_code=404, detail=f'An invoice with an id of {invoice_id} was not found.')
        invoice = parse_obj_as(Invoice, dict(row))
    return invoice


@router.post("/", response_model=InvoiceAnalyzeResult)
async def analyze_invoice(
    file: UploadFile = File(...),
    vendor_id: int = Form(...),
    pool = Depends(get_db_connection_pool),
    storage_service = Depends(get_storage_service),
    doc_intelligence_service = Depends(get_azure_doc_intelligence_service)
    ):
    """Analyze an Invoice document and create a new invoice in the database."""
    try:
        # Get vendor_id from vendor_id
        async with pool.acquire() as conn:
            vendor_id = await conn.fetchval('SELECT id FROM vendors WHERE id = $1;', vendor_id)
            if vendor_id is None:
                raise HTTPException(status_code=404, detail=f'A vendor with an id of {vendor_id} was not found.')

        # Upload file to Azure Blob Storage
        documentName = await storage_service.save_invoice_document(vendor_id, file)
        
        # Analyze the document
        document_data = await storage_service.download_blob(documentName)
        analysis_result = await doc_intelligence_service.extract_text_from_invoice_document(document_data)
        
        full_text = analysis_result.full_text

        text_chunks = doc_intelligence_service.semantic_chunking(full_text)
        metadata = doc_intelligence_service.extract_invoice_metadata(full_text)

        # Incorporate extracted field values, or use default if not found
        invoice_number = metadata['number'] or f"INV-{datetime.now().strftime('%Y-%m%d')}"
        amount = metadata['amount'] or 0
        invoice_date = metadata['invoice_date'] or datetime.now().date()
        payment_status = metadata['payment_status'] or "Pending"
        sow_number = metadata['sow_number'] or None

        metadata['invoice_date'] = None # clear this since object of type date is not json serializable


        # Get Invoice ID if Invoice Number already exists for this Vendor
        invoice_id = None
        if (invoice_number is not None):
            async with pool.acquire() as conn:
                invoice_id = await conn.fetchval('SELECT id FROM invoices WHERE vendor_id = $1 AND number = $2;', vendor_id, invoice_number)


        # Get SOW ID for SOW Number in metadata, if it exists
        sow_id = 0
        if sow_number is not None:
            async with pool.acquire() as conn:
                sow_id = await conn.fetchval('SELECT id FROM sows WHERE vendor_id = $1 AND number = $2;', vendor_id, sow_number)
                if sow_id is None:
                    # Sow not found, so grab the ID of the most recent SOW
                    sow_id = await conn.fetchval('SELECT id FROM sows WHERE vendor_id = $1 ORDER BY id DESC', vendor_id)


        # Create invoice in the database
        async with pool.acquire() as conn:
            if (invoice_id is None):
                # Create new SOW
                row = await conn.fetchrow('''
                INSERT INTO invoices (vendor_id, sow_id, "number", amount, invoice_date, payment_status, document, metadata, content)
                VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8::jsonb, $9
                ) RETURNING *;
                ''', vendor_id, sow_id, invoice_number, amount, invoice_date, payment_status, documentName, json.dumps(metadata), full_text) 
            else:
                # Update existing Invoice with new document
                row = await conn.fetchrow('''
                UPDATE invoices
                SET sow_id = $1,
                    "number" = $2,
                    amount = $3,
                    invoice_date = $4,
                    payment_status = $5,
                    document = $6,
                    metadata = $7::jsonb,
                    content = $8
                WHERE id = $9
                RETURNING *;
                ''', sow_id, invoice_number, amount, invoice_date, payment_status, documentName, json.dumps(metadata), full_text, invoice_id)

            if row is None:
                raise HTTPException(status_code=500, detail=f'An error occurred while creating the Invoice.')

            invoice = parse_obj_as(Invoice, dict(row))

            # Save Invoice Line Items
            await conn.execute('''DELETE FROM invoice_line_items WHERE invoice_id = $1''', invoice.id)
            for line_item in analysis_result.line_items:
                await conn.execute('''
                    INSERT INTO invoice_line_items (invoice_id, description, amount, status, due_date) VALUES ($1, $2, $3, $4, $5);
                ''', invoice.id, line_item.description, line_item.amount, line_item.status, line_item.due_date)

        return InvoiceAnalyzeResult(hasError=False, error=None, message="Invoice analyzed successfully.", invoice=invoice)

    except Exception as e:
        print(e) # output error to console
        return InvoiceAnalyzeResult(hasError=True, error=traceback.format_exc(), message=str(e), invoice=None) 


@router.put("/{invoice_id}", response_model=Invoice)
async def update_invoice(invoice_id: int, invoice_update: InvoiceEdit, pool = Depends(get_db_connection_pool)):
    """Updates an invoice in the database."""

    invoice = await get_by_id(invoice_id, pool)
    if invoice is None:
        raise HTTPException(status_code=404, detail=f'An invoice with an id of {invoice_id} was not found.')

    invoice.vendor_id = invoice_update.vendor_id
    invoice.sow_id = invoice_update.sow_id
    invoice.number = invoice_update.number
    invoice.amount = invoice_update.amount
    invoice.invoice_date = invoice_update.invoice_date
    invoice.payment_status = invoice_update.payment_status

    async with pool.acquire() as conn:
        row = await conn.fetchrow('''
        UPDATE invoices
        SET number = $1, amount = $2, invoice_date = $3, payment_status = $4, vendor_id = $5, sow_id = $6
        WHERE id = $7
        RETURNING *;
        ''', invoice.number, invoice.amount, invoice.invoice_date, invoice.payment_status, invoice.vendor_id, invoice.sow_id, invoice_id)
        
        updated_invoice = parse_obj_as(Invoice, dict(row))
    return updated_invoice

@router.delete("/{invoice_id}", response_model=Invoice)
async def delete_invoice(invoice_id: int, pool = Depends(get_db_connection_pool), storage_service = Depends(get_storage_service)):
    """Deletes an invoice from the database."""
    async with pool.acquire() as conn:
        row = await conn.fetchrow('SELECT * FROM invoices WHERE id = $1;', invoice_id)
        if row is None:
            raise HTTPException(status_code=404, detail=f'A invoice with an id of {id} was not found.')
        invoice = parse_obj_as(Invoice, dict(row))

        # Delete file from Azure Blob Storage
        await storage_service.delete_document(invoice.document)

        # Delete invoice from the database
        await conn.execute('DELETE FROM invoices WHERE id = $1;', invoice_id)
    return invoice