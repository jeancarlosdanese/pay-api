import pypdf


def add_password_and_restrict_printing(input_file, output_file, password):
    pdf_reader = pypdf.PdfReader(input_file)
    pdf_writer = pypdf.PdfWriter()

    for page in range(len(pdf_reader.pages)):
        pdf_writer.add_page(pdf_reader.pages[page])

    pdf_writer.encrypt(password, use_128bit=True)

    pdf_writer.write(output_file)
