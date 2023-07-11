import locale
import io
import re
import qrcode

from reportlab.pdfgen import canvas

from reportlab.lib.enums import TA_RIGHT, TA_LEFT, TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4

# from reportlab.lib.pdfencrypt import StandardEncryption
from reportlab.platypus import Paragraph, Table, Image, Spacer
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.lib.units import mm
from reportlab.graphics.barcode.common import I2of5

from app.schemas.bancos.boleto_pdf import DadosBoletoBB


TOP_MARGIN = 15 * mm
LEFT_MARGIN = 15 * mm
RIGTH_MARGIN = 15 * mm
BOTTOM_MARGIN = 15 * mm


labelStyle = ParagraphStyle("labelStyle")
labelStyle.fontName = "Helvetica"
labelStyle.fontSize = 6.5
labelStyle.alignment = TA_LEFT

rightLabelStyle = ParagraphStyle("rightLabelStyle", labelStyle)
rightLabelStyle.alignment = TA_RIGHT

dataStyle = ParagraphStyle("dataStyle")
dataStyle.fontName = "Times-Bold"
dataStyle.fontSize = 9

rightDataStyle = ParagraphStyle("rightDataStyle", dataStyle)
rightDataStyle.alignment = TA_RIGHT


# START create_boleto_bb_pdf
def create_boleto_bb_pdf(boleto: DadosBoletoBB, cpf_cnpj_senha: bool = False):
    locale.setlocale(locale.LC_ALL, "pt_BR.UTF-8")

    pagador_name = " ".join(elem.capitalize() for elem in boleto.pagador.nome.split())
    filename = str("BOLETO_" + pagador_name.replace(" ", "_") + "_" + str(boleto.numero_documento))
    # filename_path = f"downloads/{filename}.pdf"

    size = A4

    buffer = io.BytesIO()

    if cpf_cnpj_senha:
        password = re.sub(r"\D", "", boleto.pagador.cpf_cnpj)
        pdf = canvas.Canvas(buffer, pagesize=size, encrypt=password)
    else:
        pdf = canvas.Canvas(buffer, pagesize=size)

    pdf.setTitle(filename)

    __gen_boleto_bb_page(pdf, size, boleto)

    pdf.save()

    buffer.seek(0)

    # return filename_path
    return buffer


# START create_teste_pdf
def __gen_boleto_bb_page(pdf: canvas.Canvas, size, boleto: DadosBoletoBB, bookmark=False):
    # for font in pdf.getAvailableFonts():
    #     print(font)

    pdf.setPageSize(size)

    width, height = size

    height_list = [
        height * 0.229,  # header (22,9%)
        height * 0.257,  # body (25,6%)
        height * 0.414,  # footer (41,1%)
        height * 0.100,  # footer (10,40%)
    ]

    print(boleto.qr_code)

    mainTable = Table(
        [
            [__gen_pix_table(width, height_list[0], boleto.qr_code)],
            [__gen_recibo_pagador_table(width, height_list[1], boleto)],
            [__gen_boleto_bb(width, height_list[2], boleto)],
            [__gen_codigo_barras(pdf, width, height_list[3], boleto.codigo_barras)],
        ],
        colWidths=width,
        rowHeights=height_list,
    )

    mainTable.setStyle(
        [
            # ("GRID", (0, 0), (-1, -1), 1, "red"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]
    )

    mainTable.wrapOn(pdf, 0, 0)
    mainTable.drawOn(pdf, 0, 0)

    page_number = pdf.getPageNumber()
    x = width * 92 / 100  # width - (width * 8 / 100)
    y = height_list[-1] * 25 / 100

    pdf.setFillColor("white")

    page_number_text = f"Page {page_number}"
    pdf.drawString(x, y, page_number_text)

    if bookmark:
        id = f"p{page_number}"
        pdf.bookmarkPage(id)
        pdf.addOutlineEntry(page_number_text, id)

    pdf.showPage()  # Page Break


def __gen_pix_table(width, height, data_qr_code: str):
    width -= LEFT_MARGIN + RIGTH_MARGIN
    height -= TOP_MARGIN

    widths_list = [
        LEFT_MARGIN,  # left_margin
        width * 0.711,  # left_image
        width * 0.289,  # right_image
        RIGTH_MARGIN,  # right_margin
    ]

    titleStyle = ParagraphStyle("titleStyle")
    titleStyle.fontSize = 9
    titleStyle.fontName = "Times-Italic"
    titleStyle.alignment = TA_RIGHT

    left_text = Paragraph("Caso queira pagar via Pix; use o QrCode ao lado", titleStyle)

    qr = qrcode.QRCode(
        version=5,  # defines dimensions of the qr code (LxB)
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # About 30% or fewer errors can be corrected.
        box_size=5,  # defines dimensions of the box that contains QRcode
        border=5,
    )
    qr.add_data(data_qr_code)
    qr.make(fit=True)

    qr_code = QrCodeWidget(data_qr_code)
    qr_code.barWidth = height
    qr_code.barHeight = height
    drawing = Drawing(0, 0)
    drawing.add(qr_code)

    res = Table(
        [[None, left_text, drawing, None]],
        widths_list,
        height,
    )

    res.setStyle(
        [
            # ("GRID", (0, 0), (-1, -1), 1, "red"),
            ("ALIGN", (1, 0), (1, 0), "CENTER"),
            ("VALIGN", (1, 0), (1, 0), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            # ("FONTSIZE", (2, 0), (4, 0), 20),
            # ("FONTNAME", (2, 0), (3, 0), "Helvetica-Bold"),
            # ("FONTNAME", (4, 0), (4, 0), "Lateef-Regular (Arabe)"),
            # ("TEXTCOLOR", (2, 0), (2, 0), "rgba(0,0,0, 0.8)"),
            # ("TEXTCOLOR", (3, 0), (3, 0), "red"),
            # ("LEFTPADDING", (2, 0), (2, 0), -widths_list[1]),
            # ("LEFTPADDING", (3, 0), (3, 0), -widths_list[1] - 2),
            # ("LEFTPADDING", (4, 0), (4, 0), -widths_list[1]),
            # ("BOTTOMPADDING", (2, 0), (2, 0), height * 20 / 100),
            # ("BOTTOMPADDING", (3, 0), (3, 0), height * 20 / 100 + 2),
            # ("BOTTOMPADDING", (4, 0), (4, 0), height * 5 / 100),
        ]
    )

    return res


def __gen_recibo_pagador_table(width, height, boleto: DadosBoletoBB):
    # START: Recibo do pagado
    width -= LEFT_MARGIN + RIGTH_MARGIN

    num_cols = 36
    widths_list = []
    widths_list.append(LEFT_MARGIN)
    for i in range(num_cols):
        widths_list.append(width / num_cols)
    widths_list.append(RIGTH_MARGIN)

    height_recibo_pagador = 7 / 76 * height
    height_logo = 10 / 76 * height
    height_pagador = 15 / 76 * height
    height_nosso_numero = 10 / 76 * height
    height_beneficiario = 15 / 76 * height
    height_agencia = height - (
        height_recibo_pagador + height_logo + height_pagador + height_nosso_numero + height_beneficiario
    )
    heights_list = [
        height_recibo_pagador,
        height_logo,
        height_pagador,
        height_nosso_numero,
        height_beneficiario,
        height_agencia,
    ]

    linha = []
    for i in range(num_cols + 2):
        linha.append("")

    ln_recibo_pagador = linha[:]
    ln_recibo_pagador[1] = Paragraph("Recibo do Pagador", rightLabelStyle)

    # START: Linha de logo
    ln_logo = linha[:]
    logo_path = "static/logos/banco_do_brasil_pb.png"
    logo_width = width / num_cols * 11
    logo_img = Image(logo_path, logo_width, height_logo, kind="proportional")
    ln_logo[1] = logo_img
    bankIdStyle = ParagraphStyle("bankIdStyle", dataStyle)
    bankIdStyle.fontSize = 11.8
    bankIdStyle.alignment = TA_CENTER

    ln_logo[12] = Paragraph("<i>001-9</i>", bankIdStyle)
    ln_logo[15] = Paragraph(f"{boleto.linha_digitavel}", bankIdStyle)
    # END: Linha de logo

    # START: Linha de pagador
    ln_pagador = linha[:]
    ln_pagador[1] = [
        Paragraph("Nome do Pagador/CPF/CNPJ/Endereço", labelStyle),
        Paragraph(boleto.pagador.nome, dataStyle),
        Paragraph(f"{boleto.pagador.endereco}", dataStyle),
    ]
    ln_pagador[28] = [
        (Paragraph(f"CPF/CNPJ: {boleto.pagador.cpf_cnpj}", rightDataStyle)),
    ]
    # END: Linha de pagador

    # START: Linha de nosso número
    ln_nosso_numero = linha[:]
    ln_nosso_numero[1] = [
        (Paragraph("Nosso Número", labelStyle)),
        (Paragraph(f"{boleto.nosso_numero}", dataStyle)),
    ]
    ln_nosso_numero[10] = [
        (Paragraph("Nº do documento", labelStyle)),
        (Paragraph(f"{boleto.numero_documento}", dataStyle)),
    ]
    ln_nosso_numero[18] = [
        (Paragraph("Data de vencimento", labelStyle)),
        (Paragraph(f"{boleto.data_vencimento_format}", dataStyle)),
    ]
    ln_nosso_numero[24] = [
        (Paragraph("Valor do documento", labelStyle)),
        (Paragraph(f"{boleto.valor_original_format}", dataStyle)),
    ]
    ln_nosso_numero[31] = [
        (Paragraph("(=) Valor pago", labelStyle)),
        (Paragraph(" ", dataStyle)),
    ]
    # END: Linha de nosso número

    # START: Linha de beneficiario
    ln_beneficiario = linha[:]
    ln_beneficiario[1] = [
        Paragraph("Nome do Beneficiário/CPF/CNPJ/Endereço", labelStyle),
        Paragraph(boleto.beneficiario.nome, dataStyle),
        Paragraph(f"{boleto.beneficiario.endereco}", dataStyle),
    ]
    cpfCnpjStyle = ParagraphStyle("cpfCnpjStyle", dataStyle)
    cpfCnpjStyle.alignment = TA_RIGHT
    ln_beneficiario[27] = [
        (Paragraph(f"CPF/CNPJ: {boleto.beneficiario.cpf_cnpj}", cpfCnpjStyle)),
    ]
    # END: Linha de beneficiario

    # START: Linha de agencia
    ln_agencia = linha[:]
    ln_agencia[1] = [
        Paragraph("Agência/Código do Beneficiário", labelStyle),
        Paragraph(f"{boleto.beneficiario.agencia}/{boleto.beneficiario.conta}", dataStyle),
    ]
    cpfCnpjStyle = ParagraphStyle("cpfCnpjStyle", dataStyle)
    cpfCnpjStyle.alignment = TA_RIGHT
    ln_agencia[28] = [
        (Paragraph("Autenticação mecânica", rightLabelStyle)),
    ]
    # END: Linha de agencia

    res = Table(
        [
            ln_recibo_pagador,
            ln_logo,
            ln_pagador,
            ln_nosso_numero,
            ln_beneficiario,
            ln_agencia,
        ],
        widths_list,
        heights_list,
    )

    res.setStyle(
        [
            # configuração inicial
            # ("GRID", (0, 0), (-1, -1), 1, "rgba(233,30,99, 0.35)"),
            ("LINEABOVE", (1, 0), (num_cols, 0), 1, "rgba(0,0,0, 0.8)", None, (1, 1)),  # "rgba(0,0,0, 0.8)"
            ("LINEBELOW", (1, 5), (num_cols, 5), 1, "rgba(0,0,0, 0.8)", None, (1, 1)),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 0.3 * mm),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5 * mm),
            ("LEFTPADDING", (0, 0), (-1, -1), 1.5 * mm),
            ("RIGHTPADDING", (0, 0), (-1, -1), 1 * mm),
            # linha 0 (zero) ln_recibo_pagador
            ("SPAN", (1, 0), (num_cols, 0)),
            # linha 1 (um) ln_logo
            # ("LINEBEFORE", (1, 1), (1, 1), 1.5, "rgba(0,0,0, 0.8)"),
            ("LINEBEFORE", (15, 1), (num_cols, 1), 2.5, "rgba(0,0,0, 0.8)"),
            ("LINEBELOW", (1, 1), (num_cols, 1), 2, "rgba(0,0,0, 0.8)"),
            ("BOTTOMPADDING", (1, 1), (11, 1), 1.1),
            ("LEFTPADDING", (1, 1), (11, 1), -0.75),
            ("SPAN", (1, 1), (11, 1)),
            ("SPAN", (12, 1), (14, 1)),
            ("SPAN", (15, 1), (num_cols, 1)),
            # linha 2 (dois) ln_pagador
            ("LINEBEFORE", (1, 2), (1, 2), 1.5, "rgba(0,0,0, 0.8)"),
            ("LINEBELOW", (1, 2), (num_cols, 2), 1.5, "rgba(0,0,0, 0.8)"),
            ("SPAN", (1, 2), (27, 2)),
            ("SPAN", (28, 2), (num_cols, 2)),
            ("ALIGN", (28, 2), (num_cols, 2), "RIGHT"),
            # linha 3 (três) ln_nosso_numero
            ("LINEBEFORE", (1, 3), (num_cols, 3), 1.5, "rgba(0,0,0, 0.8)"),
            ("LINEBELOW", (1, 3), (num_cols, 3), 1.5, "rgba(0,0,0, 0.8)"),
            ("SPAN", (1, 3), (9, 3)),
            ("SPAN", (10, 3), (17, 3)),
            ("SPAN", (18, 3), (23, 3)),
            ("SPAN", (24, 3), (30, 3)),
            ("VALIGN", (31, 3), (num_cols, 3), "TOP"),
            ("SPAN", (31, 3), (num_cols, 3)),
            # linha 4 (quatro) ln_beneficiario
            ("LINEBEFORE", (1, 4), (1, 4), 1.5, "rgba(0,0,0, 0.8)"),
            ("LINEBELOW", (1, 4), (num_cols, 4), 1.5, "rgba(0,0,0, 0.8)"),
            ("SPAN", (1, 4), (26, 4)),
            ("SPAN", (27, 4), (num_cols, 4)),
            ("ALIGN", (27, 4), (num_cols, 4), "RIGHT"),
            # linha 5 (cinco) ln_agencia
            ("SPAN", (1, 5), (27, 5)),
            ("SPAN", (28, 5), (num_cols, 5)),
            ("ALIGN", (28, 5), (num_cols, 5), "RIGHT"),
        ]
    )

    return res
    # END: Recibo do pagado


def __gen_boleto_bb(width, height, boleto: DadosBoletoBB):
    # config extra styles
    infoStyle = ParagraphStyle("dataStyle")
    infoStyle.fontName = "Times-Roman"
    infoStyle.fontSize = 9

    # START: Recibo do pagado
    width -= LEFT_MARGIN + RIGTH_MARGIN

    num_cols = 36
    widths_list = []
    widths_list.append(LEFT_MARGIN)
    for i in range(num_cols):
        widths_list.append(width / num_cols)
    widths_list.append(RIGTH_MARGIN)

    height_10MM = 10 / 122 * height
    height_pontilhada = 5 / 122 * height
    height_pagador = height - ((height_10MM * 10) + height_pontilhada)
    heights_list = [
        height_10MM,
        height_10MM,
        height_10MM,
        height_10MM,
        height_10MM,
        height_10MM,
        height_10MM,
        height_10MM,
        height_10MM,
        height_pontilhada,
        height_pagador,
        height_10MM,
    ]

    linha = []
    for i in range(num_cols + 2):
        linha.append("")

    # START linha 0 (zero) ln_branca
    ln_branca = linha[:]
    ln_branca[1] = ""
    # END linha 0 (zero) ln_branca

    # START linha 1 (um) ln_logo
    ln_logo = linha[:]
    logo_path = "static/logos/banco_do_brasil_pb.png"
    logo_width = width / num_cols * 11
    logo_img = Image(logo_path, logo_width, height_10MM, kind="proportional")
    ln_logo[1] = logo_img
    bankIdStyle = ParagraphStyle("bankIdStyle", dataStyle)
    bankIdStyle.fontSize = 11.8
    bankIdStyle.alignment = TA_CENTER

    ln_logo[12] = Paragraph("<i>001-9</i>", bankIdStyle)
    ln_logo[15] = Paragraph(f"{boleto.linha_digitavel}", bankIdStyle)
    # END linha 1 (um) ln_logo

    # START linha 2 (dois) ln_local_pag
    ln_local_pag = linha[:]
    ln_local_pag[1] = [
        Paragraph("Local de pagamento", labelStyle),
        Paragraph(f"{boleto.local_pagamento}", dataStyle),
    ]
    ln_local_pag[27] = [
        Paragraph("Data de vencimento", labelStyle),
        Paragraph(f"{boleto.data_vencimento_format}", dataStyle),
    ]
    # END linha 2 (dois) ln_local_pag

    # START linha 3 (três) ln_beneficiario
    ln_beneficiario = linha[:]
    ln_beneficiario[1] = [
        Paragraph("Nome do beneficiário/CPF/CNPJ", labelStyle),
        Paragraph(f"{boleto.beneficiario.nome} - CPF/CNPJ: {boleto.beneficiario.cpf_cnpj}", dataStyle),
    ]
    ln_beneficiario[27] = [
        Paragraph("Agência/Código do beneficiário", labelStyle),
        Paragraph(f"{boleto.beneficiario.agencia}/{boleto.beneficiario.conta}", dataStyle),
    ]
    # END linha 3 (três) ln_beneficiario

    # START linha 4 (quatro) ln_data_doc
    ln_data_doc = linha[:]
    ln_data_doc[1] = [
        Paragraph("Data do documento", labelStyle),
        Paragraph(f"{boleto.data_documento_format}", dataStyle),
    ]
    ln_data_doc[6] = [
        Paragraph("Nº do documento", labelStyle),
        Paragraph(f"{boleto.numero_documento}", dataStyle),
    ]
    ln_data_doc[16] = [
        Paragraph("Espécie doc.", labelStyle),
        Paragraph(f"{boleto.especie_documento}", dataStyle),
    ]
    ln_data_doc[20] = [
        Paragraph("Aceite", labelStyle),
        Paragraph(f"{boleto.aceite}", dataStyle),
    ]
    ln_data_doc[22] = [
        Paragraph("Data processamento", labelStyle),
        Paragraph(f"{boleto.data_processamento_format}", dataStyle),
    ]
    ln_data_doc[27] = [
        Paragraph("Nosso Número", labelStyle),
        Paragraph(f"{boleto.nosso_numero}", dataStyle),
    ]
    # END linha 4 (quatro) ln_data_doc

    # START linha 5 (cinco) ln_uso_banco
    ln_uso_banco = linha[:]
    ln_uso_banco[1] = [
        Paragraph("Uso do banco", labelStyle),
    ]
    ln_uso_banco[6] = [
        Paragraph("Carteira", labelStyle),
        Paragraph(f"{boleto.carteira}", dataStyle),
    ]
    ln_uso_banco[11] = [
        Paragraph("Espécie", labelStyle),
        Paragraph(f"{boleto.especie}", dataStyle),
    ]
    ln_uso_banco[16] = [
        Paragraph("Quantidade", labelStyle),
    ]
    ln_uso_banco[22] = [
        Paragraph("(x) Valor", labelStyle),
    ]
    ln_uso_banco[27] = [
        Paragraph("(=) Valor do documento", labelStyle),
        Paragraph(f"{boleto.valor_original_format}", dataStyle),
    ]
    # END linha 5 (cinco) ln_uso_banco

    # START linha 6 (seis) ln_info_desc
    ln_info_desc = linha[:]
    ln_info_desc[1] = [
        Paragraph("Informações de responsabilidade do beneficiário", labelStyle),
        Paragraph(f"{boleto.mensagem_juros}", infoStyle),
        Paragraph(f"{boleto.mensagem_multa}", infoStyle),
        Paragraph(f"{boleto.mensagem_desconto}", infoStyle),
        Spacer(1, 7),
        Paragraph(f"{boleto.mensagem_dias_recebimento}", infoStyle),
        Spacer(1, 5),
        Paragraph(f"{boleto.mensagem_beneficiario}", infoStyle),
    ]
    ln_info_desc[27] = [
        Paragraph("(-) Desconto/Abatimento", labelStyle),
        Paragraph("0,00", dataStyle),
    ]
    # END linha 6 (seis) ln_info_desc

    # START linha 7 (sete) ln_info_multa
    ln_info_multa = linha[:]
    ln_info_multa[27] = [
        Paragraph("(+) Juros/Multa", labelStyle),
        Paragraph("0,00", dataStyle),
    ]
    # END linha 7 (sete) ln_info_multa

    # START linha 8 (oito) ln_info_cobr
    ln_info_cobr = linha[:]
    ln_info_cobr[27] = [
        Paragraph("(=) Valor cobrado", labelStyle),
        Paragraph(f"{boleto.valor_original_format}", dataStyle),
    ]
    # END linha 8 (oito) ln_info_cobr

    # START linha 9 (dez) ln_pontilhada
    ln_pontilhada = linha[:]
    ln_pontilhada[1] = ""
    # END linha 9 (dez) ln_pontilhada

    # START linha 10 (nove) ln_pagador
    ln_pagador = linha[:]
    ln_pagador[1] = [
        Paragraph("Nome do pagador/CPF/CNPJ/Endereço", labelStyle),
        Paragraph(f"{boleto.pagador.nome}", dataStyle),
        Paragraph(f"{boleto.pagador.endereco}", dataStyle),
    ]
    ln_pagador[27] = [
        Paragraph(f"CPF/CNPJ: {boleto.pagador.cpf_cnpj}", rightDataStyle),
    ]
    # END linha 10 (nove) ln_pagador

    # START linha 11 (onze) ln_fechamente
    ln_fechamento = linha[:]
    ln_fechamento[1] = [
        Paragraph("Beneficiário final", labelStyle),
    ]
    ln_fechamento[19] = [
        Paragraph("Autenticação mecânica - Finha de compensação", rightLabelStyle),
    ]
    # ENDS linha 11 (onze) ln_fechamente

    res = Table(
        [
            ln_branca,
            ln_logo,
            ln_local_pag,
            ln_beneficiario,
            ln_data_doc,
            ln_uso_banco,
            ln_info_desc,
            ln_info_multa,
            ln_info_cobr,
            ln_pontilhada,
            ln_pagador,
            ln_fechamento,
        ],
        widths_list,
        heights_list,
    )

    res.setStyle(
        [
            # configuração inicial
            # ("GRID", (0, 0), (-1, -1), 1, "rgba(233,30,99, 0.35)"),
            ("LINEABOVE", (1, 0), (num_cols, 0), 1, "rgba(0,0,0, 0.8)", None, (1, 1)),  # "rgba(0,0,0, 0.8)"
            ("LINEBELOW", (1, 5), (num_cols, 5), 1, "rgba(0,0,0, 0.8)", None, (1, 1)),
            ("LINEBELOW", (1, 9), (num_cols, 9), 1, "rgba(0,0,0, 0.8)", None, (1, 1)),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 0.3 * mm),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5 * mm),
            ("LEFTPADDING", (0, 0), (-1, -1), 1.5 * mm),
            ("RIGHTPADDING", (0, 0), (-1, -1), 1 * mm),
            ("VALIGN", (1, 2), (-1, -1), "TOP"),
            # linha 0 (zero) ln_recibo_pagador
            ("SPAN", (1, 0), (num_cols, 0)),
            # linha 1 (um) ln_logo
            # ("LINEBEFORE", (1, 1), (1, 1), 1.5, "rgba(0,0,0, 0.8)"),
            ("LINEBEFORE", (15, 1), (num_cols, 1), 2.5, "rgba(0,0,0, 0.8)"),
            ("LINEBELOW", (1, 1), (num_cols, 1), 2, "rgba(0,0,0, 0.8)"),
            ("BOTTOMPADDING", (1, 1), (11, 1), 1.1),
            ("LEFTPADDING", (1, 1), (11, 1), -0.75),
            ("SPAN", (1, 1), (11, 1)),
            ("SPAN", (12, 1), (14, 1)),
            ("SPAN", (15, 1), (num_cols, 1)),
            # linha 2 (dois) ln_local_pag
            ("LINEBEFORE", (1, 2), (27, 2), 1.5, "rgba(0,0,0, 0.8)"),
            ("LINEBELOW", (1, 2), (num_cols, 2), 1.5, "rgba(0,0,0, 0.8)"),
            ("SPAN", (1, 2), (26, 2)),
            ("SPAN", (27, 2), (num_cols, 2)),
            # linha 3 (três) ln_beneficiario
            ("LINEBEFORE", (1, 3), (27, 3), 1.5, "rgba(0,0,0, 0.8)"),
            ("LINEBELOW", (1, 3), (num_cols, 3), 1.5, "rgba(0,0,0, 0.8)"),
            ("SPAN", (1, 3), (26, 3)),
            ("SPAN", (27, 3), (num_cols, 3)),
            # linha 4 (quatro) ln_data_doc
            ("LINEBEFORE", (1, 4), (num_cols, 4), 1.5, "rgba(0,0,0, 0.8)"),
            ("LINEBELOW", (1, 4), (num_cols, 4), 1.5, "rgba(0,0,0, 0.8)"),
            ("SPAN", (1, 4), (5, 4)),
            ("SPAN", (6, 4), (15, 4)),
            ("SPAN", (16, 4), (19, 4)),
            ("SPAN", (20, 4), (21, 4)),
            ("SPAN", (22, 4), (26, 4)),
            ("SPAN", (27, 4), (num_cols, 4)),
            # linha 5 (cinco) ln_uso_banco
            ("LINEBEFORE", (1, 5), (num_cols, 5), 1.5, "rgba(0,0,0, 0.8)"),
            ("LINEBELOW", (1, 5), (num_cols, 5), 1.5, "rgba(0,0,0, 0.8)"),
            ("SPAN", (1, 5), (5, 5)),
            ("SPAN", (6, 5), (10, 5)),
            ("SPAN", (11, 5), (15, 5)),
            ("SPAN", (16, 5), (21, 5)),
            ("SPAN", (22, 5), (26, 5)),
            ("SPAN", (27, 5), (num_cols, 5)),
            # linha 6 (seis) somente info (1, 6) (26, 9)
            ("LINEBEFORE", (1, 6), (num_cols, 6), 1.5, "rgba(0,0,0, 0.8)"),
            ("LINEBELOW", (1, 6), (num_cols, 6), 1.5, "rgba(0,0,0, 0.8)"),
            ("SPAN", (1, 6), (26, 9)),
            # linha 6 (seis) (27, 6) ln_info_desc
            ("SPAN", (27, 6), (num_cols, 6)),
            # linha 7 (sete) (27, 7) ln_info_multa
            ("LINEBEFORE", (1, 7), (num_cols, 7), 1.5, "rgba(0,0,0, 0.8)"),
            ("LINEBELOW", (1, 7), (num_cols, 7), 1.5, "rgba(0,0,0, 0.8)"),
            ("SPAN", (27, 7), (num_cols, 7)),
            # linha 8 (oito) (27, 7) ln_info_combr
            ("LINEBEFORE", (1, 8), (num_cols, 8), 1.5, "rgba(0,0,0, 0.8)"),
            ("LINEBELOW", (1, 8), (num_cols, 8), 1.5, "rgba(0,0,0, 0.8)"),
            ("SPAN", (27, 8), (num_cols, 8)),
            # linha 9 (nove) (27, 9) ln_info_combr
            ("LINEBEFORE", (1, 9), (1, 9), 1.5, "rgba(0,0,0, 0.8)"),
            ("SPAN", (27, 9), (num_cols, 9)),
            # linha 10 (dez) (27, 9) ln_pagador
            ("SPAN", (1, 10), (num_cols, 10)),
            ("SPAN", (27, 10), (num_cols, 10)),
            ("VALIGN", (0, 10), (num_cols, 10), "MIDDLE"),
            ("LINEBELOW", (1, 10), (num_cols, 10), 1.5, "rgba(0,0,0, 0.8)"),
            # linha 11 (onze) (27, 9) ln_fechamento
            ("SPAN", (1, 11), (18, 11)),
            ("SPAN", (19, 11), (num_cols, 11)),
            ("TOPPADDING", (1, 11), (num_cols, 11), 0.8 * mm),
        ]
    )

    return res


def __gen_codigo_barras(pdf, width, height, codigo_barra_numerico: str):
    width -= LEFT_MARGIN + RIGTH_MARGIN
    # height -= BOTTOM_MARGIN

    widths_list = [
        LEFT_MARGIN,  # left_margin
        width,  # right_image
        RIGTH_MARGIN,  # right_margin
    ]

    titleStyle = ParagraphStyle("titleStyle")
    titleStyle.fontSize = 9
    titleStyle.fontName = "Times-Italic"
    titleStyle.alignment = TA_RIGHT

    frame = __codigo_barra_i25(pdf, codigo_barra_numerico, LEFT_MARGIN, BOTTOM_MARGIN)

    res = Table(
        [[None, frame, None]],
        widths_list,
        height,
    )

    res.setStyle(
        [
            # ("GRID", (0, 0), (-1, -1), 1, "red"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 15 * mm),
            # ("ALIGN", (1, 0), (1, 0), "CENTER"),
            # ("VALIGN", (1, 0), (1, 0), "MIDDLE"),
            # ("LEFTPADDING", (0, 0), (-1, -1), 0),
            # ("FONTSIZE", (2, 0), (4, 0), 20),
            # ("FONTNAME", (2, 0), (3, 0), "Helvetica-Bold"),
            # ("FONTNAME", (4, 0), (4, 0), "Lateef-Regular (Arabe)"),
            # ("TEXTCOLOR", (2, 0), (2, 0), "rgba(0,0,0, 0.8)"),
            # ("TEXTCOLOR", (3, 0), (3, 0), "red"),
            # ("LEFTPADDING", (2, 0), (2, 0), -widths_list[1]),
            # ("LEFTPADDING", (3, 0), (3, 0), -widths_list[1] - 2),
            # ("LEFTPADDING", (4, 0), (4, 0), -widths_list[1]),
            # ("BOTTOMPADDING", (2, 0), (2, 0), height * 20 / 100),
            # ("BOTTOMPADDING", (3, 0), (3, 0), height * 20 / 100 + 2),
            # ("BOTTOMPADDING", (4, 0), (4, 0), height * 5 / 100),
        ]
    )

    return res


def __codigo_barra_i25(pdf, num, x, y):
    """Imprime Código de barras otimizado para boletos

    O código de barras é otmizado para que o comprimeto seja sempre o
    estipulado pela febraban de 103mm.

    """
    # http://en.wikipedia.org/wiki/Interleaved_2_of_5

    altura = 15 * mm
    comprimento = 120 * mm

    thin_bar = 0.254320987654 * mm  # Tamanho correto aproximado

    bc = I2of5(num, barWidth=thin_bar, ratio=3, barHeight=altura, bearers=0, quiet=0, checksum=0)

    # Recalcula o tamanho do thin_bar para que o cod de barras tenha o
    # comprimento correto
    thin_bar = (thin_bar * comprimento) / bc.width
    bc.__init__(num, barWidth=thin_bar)

    bc.drawOn(pdf, x, y)
