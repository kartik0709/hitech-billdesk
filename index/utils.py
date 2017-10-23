import io
import os

import xlsxwriter
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import get_template
from django.utils.timezone import localtime
from xhtml2pdf import pisa


# used for locating static files
def link_callback(uri, rel):
    """
    Convert HTML URIs to absolute system paths so xhtml2pdf can access those
    resources
    """
    # use short variable names
    s_url = settings.STATIC_URL      # Typically /static/
    s_root = settings.STATIC_ROOT    # Typically /home/userX/project_static/
    m_url = settings.MEDIA_URL       # Typically /static/media/
    m_root = settings.MEDIA_ROOT     # Typically /home/userX/project_static/media/

    # convert URIs to absolute system paths
    if uri.startswith(m_url):
        path = os.path.join(m_root, uri.replace(m_url, ""))
    elif uri.startswith(s_url):
        path = os.path.join(s_root, uri.replace(s_url, ""))
    else:
        return uri  # handle absolute uri (ie: http://some.tld/foo.png)

    # make sure that file exists
    if not os.path.isfile(path):
        raise Exception(
            'media URI must start with {} or {}'.format(s_url, m_url)
        )
    return path


# function to render pdf file, first parameter is for which template to use, second parameter is for context
# of that template
def render_to_pdf(pdfname, template, context):

    # Create a Django response object, and specify content_type as pdf
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'filename={}.pdf'.format(pdfname)

    # find the template and render it.
    template = get_template(template)
    html = template.render(context)

    # create a pdf
    pisa_status = pisa.CreatePDF(html, dest=response, link_callback=link_callback)
    # if error then show some funny view
    if pisa_status.err:
        return HttpResponse('We had some errors')
    return response


# function to render excel file, first 3 parameters of function are for heading of excel file while the
# fourth parameter is for data itself
def write_to_excel(t_type, date_from, date_to, transaction):
    # opens a byte stream to write excel file
    output = io.BytesIO()

    # adds workbook to excel file
    workbook = xlsxwriter.Workbook(output)

    # adds worksheet to workbook by the name of summary
    worksheet = workbook.add_worksheet("summary")

    # defines style with different formats
    title = workbook.add_format({
        'bold': True,
        'font_size': 14,
        'align': 'center',
        'valign': 'vcenter'
    })
    header = workbook.add_format({
        'bg_color': '#F7F7F7',
        'color': 'black',
        'align': 'center',
        'valign': 'top',
        'border': 1
    })

    # sets the title
    title_text = "{0} {1} {2} {3} {4}".format(t_type, "summary from", date_from, "to", date_to)
    # merges columns to form one big title
    worksheet.merge_range('A2:G2', title_text, title)

    # writes the heading of columns
    worksheet.write(4, 0, "Transaction ID", header)
    worksheet.write(4, 1, "Date-time", header)
    worksheet.write(4, 2, "PID", header)
    worksheet.write(4, 3, "Quantity", header)
    worksheet.write(4, 4, "Tax", header)
    worksheet.write(4, 5, "Total", header)
    worksheet.write(4, 6, "Type", header)

    # adds another style which centers the text in the cell
    style_format = workbook.add_format()
    style_format.set_center_across()

    # enumerates over data to form rows
    for idx, data in enumerate(transaction):
        # makes sure that writing new rows begins from row 6 because first 5 rows are reserved for headings
        row = 5 + idx
        worksheet.write_number(row, 0, data.id, style_format)
        worksheet.write_string(row, 1, str(localtime(data.datetime)).split(".", 1)[0], style_format)
        worksheet.write(row, 2, str(data.pid), style_format)
        worksheet.write(row, 3, data.quantity, style_format)
        # if transaction is purchase, turn its price and tax in negatives
        if data.type == "purchase":
            worksheet.write(row, 4, -data.tax)
            worksheet.write(row, 5, -data.total)
        elif data.type == "sale":
            worksheet.write(row, 4, data.tax)
            worksheet.write(row, 5, data.total)
        worksheet.write(row, 6, data.type, style_format)

    # increases the width of the columns
    worksheet.set_column('A:A', 14)
    worksheet.set_column('B:B', 20)
    worksheet.set_column('C:C', 17)
    worksheet.set_column('D:D', 14)
    worksheet.set_column('E:E', 14)
    worksheet.set_column('F:F', 14)
    worksheet.set_column('G:G', 14)

    # adds formulas on the last row for total tax and total price
    worksheet.write_formula(
        row + 1, 4, '=sum({0}{1}:{0}{2})'.format('E', 6, row + 1))

    worksheet.write_formula(
        row+1, 5, '=sum({0}{1}:{0}{2})'.format('F', 6, row+1))

    # saves workbook
    workbook.close()

    # passes data into a variable to write it in response
    xlsx_data = output.getvalue()

    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename=Report.xlsx'

    response.write(xlsx_data)
    return response
