from typing import Optional
from pydantic import UUID4, BaseModel, condecimal, constr, validator

from pydantic.types import conint
from datetime import date
from app.schemas.bancos.beneficiario_bb import BeneficiarioBB, BeneficiarioFinalBB, BeneficiarioFull
from app.schemas.bancos.convenio_bancario import ConvenioBancarioFull
from app.schemas.bancos.pagador_bb import PagadorBB, PagadorFull
from app.schemas.bancos.qr_code_bb import QrCodeBB, QrCodeFull
from app.schemas.base import BaseSchema, DateTimeModelMixin, IDModelMixin, IDModelWithTenantMixin
from app.util.utils import to_snake_case

# from app.util.utils import get_date_print_format, get_valor_real_print_format

from app.util.utils_bb import get_date_bb, get_date_bb_format


class DescontoBB(BaseModel):
    tipo: int = 0
    dataExpiracao: Optional[date]  # data de expiração do desconto (somente se tipo > 0), no formato “dd.mm.aaaa”
    porcentagem: Optional[condecimal(decimal_places=2)] = 0  # Define a porcentagem do desconto (somente se tipo = 2)
    valor: Optional[condecimal(decimal_places=2)] = 0  # Define o valor do desconto (somente se tipo = 1)

    @validator("dataExpiracao")
    def date_equal_or_greater_than(cls, data_expiracao):
        today = date.today()
        if not data_expiracao >= today:
            raise ValueError("data_vencimento must be equal or later than the current date")
        return get_date_bb_format(date=data_expiracao)

    # class Config:
    #     alias_generator = underscore_to_camel


class JurosMoraBB(BaseModel):
    tipo: int = 2  # Domínio: 0 - Dispensar; 1 - Valor fixo por dia de atraso; 2 - Taxa mensal; 3 - Isento
    porcentagem: Optional[
        condecimal(max_digits=2)
    ] = 1.00  # noqa flake8(E501) - Define a taxa mensal de juros (somente informar se tipo = 2). A taxa incide sobre o valor atual do boleto (valorOriginal - valorAbatimento)
    valor: Optional[
        condecimal(max_digits=2)
    ] = 0  # Define o valor fixo por dia de atraso (somente informar se tipo = 1)


class MultaBB(BaseModel):
    tipo: int = 2  # noqa flake8(E501) - Domínio: 0 - Dispensar; 1 - Valor fixo (a partir da data estipulada no registro); 2 - Percentual (a partir da data estipulada no registro)
    data: date  # noqa flake8(E501) - Define a data a partir da qual será cobrada a multa (somente informar se tipo = 1 ou 2). Deve ser posterior a data de vencimento do boleto.
    porcentagem: Optional[
        condecimal(max_digits=2)
    ] = 2.00  # noqa flake8(E501) - Define a porcentagem da multa (somente informar se tipo = 2). A porcentagem incide sobre o valor atual do boleto (valorOriginal - valorAbatimento)
    valor: Optional[condecimal(max_digits=2)] = 0  # Define o valor da multa (somente informar se tipo = 1)

    @validator("data")
    def data_equal_or_greater_than(cls, data):
        return get_date_bb_format(date=data)


class BoletoBBCreate(BaseModel):
    numeroConvenio: int
    numeroCarteira: int
    numeroVariacaoCarteira: int
    codigoModalidade: int = 1
    dataEmissao: Optional[date] = None
    dataVencimento: date
    valorOriginal: condecimal()
    valorAbatimento: Optional[
        condecimal()
    ] = None  # noqa flake8(E501) - Valor de dedução do boleto. Se informado, deve ser maior que zero
    quantidadeDiasProtesto: int = 0
    quantidadeDiasNegativacao: int = 0
    orgaoNegativador: int = 0
    indicadorAceiteTituloVencido: str = "S"
    numeroDiasLimiteRecebimento: int = 30
    codigoAceite: str = "N"
    codigoTipoTitulo: int = 2
    descricaoTipoTitulo: str = "DS"
    indicadorPermissaoRecebimentoParcial: str = "N"
    numeroTituloBeneficiario: constr(min_length=1, max_length=15, strip_whitespace=True)
    campoUtilizacaoBeneficiario: Optional[constr(max_length=30, strip_whitespace=True)]
    numeroTituloCliente: constr(min_length=20, max_length=20)
    mensagemBloquetoOcorrencia: Optional[constr(max_length=165)]
    desconto: Optional[DescontoBB] = None
    segundoDesconto: Optional[DescontoBB] = None
    terceiroDesconto: Optional[DescontoBB] = None
    jurosMora: JurosMoraBB
    multa: MultaBB
    pagador: PagadorBB
    quantidadeDiasNegativacao: Optional[
        int
    ]  # noqa flake8(E501) - Quantidade de dias corridos depois do vencimento do boleto para a negativação automática, através do órgão negativador selecionado. Não confundir com protesto
    orgaoNegativador: Optional[int]  # Código do órgão negativador selecionado. Domínio: 10 - SERASA; 11 - QUOD
    beneficiarioFinal: BeneficiarioFinalBB
    indicadorPix: str = "S"  # noqa flake8(E501) - Código para informar se o boleto terá um QRCode Pix atrelado. Se não informado, ou utilizado caractere inválido, o sistema assumirá ‘N’. Atenção: conforme regulamentação do Bacen, é permitido somente para modalidade de cobrança simples (ver codigoModalidade). Domínio: S - QRCode dinâmico; N - sem Pix.

    @validator("dataEmissao")
    def date_emissao_equal_or_greater_than(cls, data_emissao):
        if not data_emissao:
            data_emissao = date.today()
        return get_date_bb_format(date=data_emissao)

    @validator("dataVencimento")
    def date_equal_or_greater_than(cls, data_vencimento):
        today = date.today()
        if not data_vencimento >= today:
            raise ValueError("dataVencimento must be equal or later than the current date")
        return get_date_bb_format(date=data_vencimento)

    # class Config:
    #     alias_generator = underscore_to_camel


class RegistroBoletoBB(BaseModel):
    numero: constr(max_length=20)
    numeroCarteira: conint()
    numeroVariacaoCarteira: conint()
    codigoCliente: conint()
    linhaDigitavel: constr(max_length=47)
    codigoBarraNumerico: constr(max_length=44)
    numeroContratoCobranca: conint()
    beneficiario: BeneficiarioBB
    qrCode: QrCodeBB


class BoletoBB(BaseSchema):
    convenio_bancario_id: UUID4
    numero_titulo_beneficiario: conint()
    data_emissao: date
    data_vencimento: date
    data_baixa_automatico: date
    valor_original: condecimal(gt=0, decimal_places=2)
    valor_desconto: Optional[condecimal()] = 0
    descricao_tipo_titulo: constr(min_length=2, max_length=2)
    numero: constr(min_length=20, max_length=20)
    mensagem_beneficiario: Optional[constr(min_length=3, max_length=30)]  # noqa
    codigo_cliente: Optional[conint()]
    linha_digitavel: Optional[constr(min_length=47, max_length=47)]
    codigo_barra_numerico: Optional[constr(min_length=44, max_length=44)]
    numero_contrato_cobranca: Optional[conint()]

    @validator("descricao_tipo_titulo")
    def validate_descricao_tipo_titulo(cls, descricao_tipo_titulo: str):
        return descricao_tipo_titulo.upper() if descricao_tipo_titulo else descricao_tipo_titulo


class BoletoBBWithTenantCreate(BoletoBB):
    tenant_id: UUID4
    pagador_bb_id: UUID4


class BoletoBBUpdate(BaseSchema):
    data_vencimento: Optional[date] = None
    data_recebimento: Optional[date] = None
    data_credito: Optional[date] = None
    valor_original: Optional[condecimal(gt=0, decimal_places=2)] = None
    valor_desconto: Optional[condecimal()] = None
    valor_pago_sacado: Optional[condecimal()] = None
    valor_credito_cedente: Optional[condecimal()] = None
    valor_desconto_utilizado: Optional[condecimal()] = None
    valor_multa_recebido: Optional[condecimal()] = None
    valor_juros_recebido: Optional[condecimal()] = None


class BoletoBBNewVencimento(BaseSchema):
    data_vencimento: date

    @property
    def data_vencimento_format(self) -> str:
        return get_date_bb_format(self.data_vencimento)

    def dict(self):
        base_dict = super().dict()
        base_dict["data_vencimento_format"] = self.data_vencimento_format
        return base_dict

    # @property
    # def data_vencimento_format(self) -> str:
    #     # return self.data_vencimento.strftime("%d/%m/%Y")
    #     return get_date_bb_format(self.data_vencimento)

    # def dict(self, **kwargs):
    #     return super().dict(**kwargs, by_alias=True, exclude_none=True) | {
    #         "data_vencimento_format": self.data_vencimento_format,
    #     }

    # @validator("data_vencimento")
    # def data_equal_or_greater_than(cls, data):


class BoletoBBAllViewFields(BoletoBBUpdate):
    pagador_bb_id: UUID4


class BoletoBBInDB(DateTimeModelMixin, BoletoBBAllViewFields, BoletoBB, IDModelWithTenantMixin):
    pass


class BoletoBBFull(BoletoBBUpdate, BoletoBB, IDModelMixin):
    convenio: Optional[ConvenioBancarioFull]
    pagador: Optional[PagadorFull]
    beneficiario: Optional[BeneficiarioFull]
    qr_code: Optional[QrCodeFull]


class BoletoBBForList(IDModelMixin):
    tipo_pessoa: Optional[str]
    cpf_cnpj: Optional[str]
    nome: Optional[str]
    telefone: Optional[str]
    numero_titulo_beneficiario: Optional[conint()]
    data_emissao: Optional[date]
    data_vencimento: Optional[date]
    valor_original: Optional[condecimal(gt=0, decimal_places=2)]
    valor_desconto: Optional[condecimal()] = 0
    descricao_tipo_titulo: Optional[constr(min_length=2, max_length=2)]
    numero: Optional[constr(min_length=20, max_length=20)]
    codigo_cliente: Optional[conint()]
    linha_digitavel: Optional[constr(min_length=47, max_length=47)]
    codigo_barra_numerico: Optional[constr(min_length=44, max_length=44)]
    numero_contrato_cobranca: Optional[conint()]


class BoletoBBRequestDetails(BaseSchema):
    id: UUID4
    numero: str
    numero_convenio: int
    client_id: str
    client_id: str
    client_secret: str
    developer_application_key: str


class BoletoBBResponseDetails(BaseSchema):
    codigoLinhaDigitavel: constr()
    textoEmailPagador: constr()
    textoMensagemBloquetoTitulo: constr()
    codigoTipoMulta: conint()
    codigoCanalPagamento: conint()
    numeroContratoCobranca: conint()
    codigoTipoInscricaoSacado: conint()
    numeroInscricaoSacadoCobranca: conint()
    codigoEstadoTituloCobranca: conint()
    codigoTipoTituloCobranca: conint()
    codigoModalidadeTitulo: conint()
    codigoAceiteTituloCobranca: constr()
    codigoPrefixoDependenciaCobrador: conint()
    codigoIndicadorEconomico: conint()
    numeroTituloCedenteCobranca: constr()
    codigoTipoJuroMora: conint()
    dataEmissaoTituloCobranca: constr()
    dataRegistroTituloCobranca: constr()
    dataVencimentoTituloCobranca: constr()
    valorOriginalTituloCobranca: condecimal()
    valorAtualTituloCobranca: condecimal()
    valorPagamentoParcialTitulo: condecimal()
    valorAbatimentoTituloCobranca: condecimal()
    percentualImpostoSobreOprFinanceirasTituloCobranca: condecimal()
    valorImpostoSobreOprFinanceirasTituloCobranca: condecimal()
    valorMoedaTituloCobranca: condecimal()
    percentualJuroMoraTitulo: condecimal()
    valorJuroMoraTitulo: condecimal()
    percentualMultaTitulo: condecimal()
    valorMultaTituloCobranca: condecimal()
    quantidadeParcelaTituloCobranca: conint()
    dataBaixaAutomaticoTitulo: constr()
    textoCampoUtilizacaoCedente: constr()
    indicadorCobrancaPartilhadoTitulo: constr()
    nomeSacadoCobranca: constr()
    textoEnderecoSacadoCobranca: constr()
    nomeBairroSacadoCobranca: constr()
    nomeMunicipioSacadoCobranca: constr()
    siglaUnidadeFederacaoSacadoCobranca: constr()
    numeroCepSacadoCobranca: conint()
    valorMoedaAbatimentoTitulo: condecimal()
    dataProtestoTituloCobranca: constr()
    codigoTipoInscricaoSacador: conint()
    numeroInscricaoSacadorAvalista: conint()
    nomeSacadorAvalistaTitulo: constr()
    percentualDescontoTitulo: condecimal()
    dataDescontoTitulo: constr()
    valorDescontoTitulo: condecimal()
    codigoDescontoTitulo: conint()
    percentualSegundoDescontoTitulo: condecimal()
    dataSegundoDescontoTitulo: constr()
    valorSegundoDescontoTitulo: condecimal()
    codigoSegundoDescontoTitulo: conint()
    percentualTerceiroDescontoTitulo: condecimal()
    dataTerceiroDescontoTitulo: constr()
    valorTerceiroDescontoTitulo: condecimal()
    codigoTerceiroDescontoTitulo: conint()
    dataMultaTitulo: constr()
    numeroCarteiraCobranca: conint()
    numeroVariacaoCarteiraCobranca: conint()
    quantidadeDiaProtesto: conint()
    quantidadeDiaPrazoLimiteRecebimento: conint()
    dataLimiteRecebimentoTitulo: constr()
    indicadorPermissaoRecebimentoParcial: constr()
    textoCodigoBarrasTituloCobranca: constr()
    codigoOcorrenciaCartorio: conint()
    valorImpostoSobreOprFinanceirasRecebidoTitulo: condecimal()
    valorAbatimentoTotal: condecimal()
    valorJuroMoraRecebido: condecimal()
    valorDescontoUtilizado: condecimal()
    valorPagoSacado: condecimal()
    valorCreditoCedente: condecimal()
    codigoTipoLiquidacao: conint()
    dataCreditoLiquidacao: constr()
    dataRecebimentoTitulo: constr()
    codigoPrefixoDependenciaRecebedor: conint()
    codigoNaturezaRecebimento: conint()
    numeroIdentidadeSacadoTituloCobranca: constr()
    codigoResponsavelAtualizacao: constr()
    codigoTipoBaixaTitulo: conint()
    valorMultaRecebido: condecimal()
    valorReajuste: condecimal()
    valorOutroRecebido: condecimal()
    codigoIndicadorEconomicoUtilizadoInadimplencia: condecimal()

    @validator("dataEmissaoTituloCobranca")
    def validate_dataEmissaoTituloCobranca(cls, data_str: str):
        return get_date_bb(data_str)

    @validator("dataRegistroTituloCobranca")
    def validate_dataRegistroTituloCobranca(cls, data_str: str):
        return get_date_bb(data_str)

    @validator("dataVencimentoTituloCobranca")
    def validate_dataVencimentoTituloCobranca(cls, data_str: str):
        return get_date_bb(data_str)

    @validator("dataBaixaAutomaticoTitulo")
    def validate_dataBaixaAutomaticoTitulo(cls, data_str: str):
        return get_date_bb(data_str)

    @validator("dataProtestoTituloCobranca")
    def validate_dataProtestoTituloCobranca(cls, data_str: str):
        return get_date_bb(data_str)

    @validator("dataDescontoTitulo")
    def validate_dataDescontoTitulo(cls, data_str: str):
        return get_date_bb(data_str)

    @validator("dataSegundoDescontoTitulo")
    def validate_dataSegundoDescontoTitulo(cls, data_str: str):
        return get_date_bb(data_str)

    @validator("dataTerceiroDescontoTitulo")
    def validate_dataTerceiroDescontoTitulo(cls, data_str: str):
        return get_date_bb(data_str)

    @validator("dataMultaTitulo")
    def validate_dataMultaTitulo(cls, data_str: str):
        return get_date_bb(data_str)

    @validator("dataLimiteRecebimentoTitulo")
    def validate_dataLimiteRecebimentoTitulo(cls, data_str: str):
        return get_date_bb(data_str)

    @validator("dataCreditoLiquidacao")
    def validate_dataCreditoLiquidacao(cls, data_str: str):
        return get_date_bb(data_str)

    @validator("dataRecebimentoTitulo")
    def validate_dataRecebimentoTitulo(cls, data_str: str):
        return get_date_bb(data_str)


class BoletoBBResponseDetailsSnake(BoletoBBResponseDetails):
    class Config:
        allow_population_by_field_name = True
        alias_generator = to_snake_case


class AlteracaoData(BaseModel):
    novaDataVencimento: str


class Desconto(BaseModel):
    tipoPrimeiroDesconto: int
    valorPrimeiroDesconto: condecimal()
    percentualPrimeiroDesconto: condecimal()
    dataPrimeiroDesconto: str
    tipoSegundoDesconto: int
    valorSegundoDesconto: condecimal()
    percentualSegundoDesconto: condecimal()
    dataSegundoDesconto: str
    tipoTerceiroDesconto: int
    valorTerceiroDesconto: condecimal()
    percentualTerceiroDesconto: condecimal()
    dataTerceiroDesconto: str


class AlteracaoDesconto(BaseModel):
    tipoPrimeiroDesconto: int
    novoValorPrimeiroDesconto: condecimal()
    novoPercentualPrimeiroDesconto: condecimal()
    novaDataLimitePrimeiroDesconto: str
    tipoSegundoDesconto: int
    novoValorSegundoDesconto: condecimal()
    novoPercentualSegundoDesconto: condecimal()
    novaDataLimiteSegundoDesconto: str
    tipoTerceiroDesconto: int
    novoValorTerceiroDesconto: condecimal()
    novoPercentualTerceiroDesconto: condecimal()
    novaDataLimiteTerceiroDesconto: str


class AlteracaoDataDesconto(BaseModel):
    novaDataLimitePrimeiroDesconto: str
    novaDataLimiteSegundoDesconto: str
    novaDataLimiteTerceiroDesconto: str


class Protesto(BaseModel):
    quantidadeDiasProtesto: int


class Abatimento(BaseModel):
    valorAbatimento: condecimal()


class AlteracaoAbatimento(BaseModel):
    novoValorAbatimento: condecimal()


class Juros(BaseModel):
    tipoJuros: int
    valorJuros: condecimal()
    taxaJuros: condecimal()


class Multa(BaseModel):
    tipoMulta: int
    valorMulta: condecimal()
    dataInicioMulta: str
    taxaMulta: condecimal()


class Negativacao(BaseModel):
    quantidadeDiasNegativacao: int
    tipoNegativacao: int


class AlteracaoSeuNumero(BaseModel):
    codigoSeuNumero: str


class AlteracaoEndereco(BaseModel):
    enderecoPagador: str
    bairroPagador: str
    cidadePagador: str
    UFPagador: str
    CEPPagador: int


class AlteracaoPrazo(BaseModel):
    quantidadeDiasAceite: int


class BoletoBBAlteracao(BaseModel):
    numeroConvenio: int
    indicadorNovaDataVencimento: str = "N"
    alteracaoData: Optional[AlteracaoData] = None
    indicadorAtribuirDesconto: str = "N"
    desconto: Optional[Desconto] = None
    indicadorAlterarDesconto: str = "N"
    alteracaoDesconto: Optional[AlteracaoDesconto] = None
    indicadorAlterarDataDesconto: str = "N"
    alteracaoDataDesconto: Optional[AlteracaoDataDesconto] = None
    indicadorProtestar: str = "N"
    protesto: Optional[Protesto] = None
    indicadorSustacaoProtesto: str = "N"
    indicadorCancelarProtesto: str = "N"
    indicadorIncluirAbatimento: str = "N"
    abatimento: Optional[Abatimento] = None
    indicadorAlterarAbatimento: str = "N"
    alteracaoAbatimento: Optional[AlteracaoAbatimento] = None
    indicadorCobrarJuros: str = "N"
    juros: Optional[Juros] = None


class BoletoBBBaixar(BaseModel):
    numeroConvenio: int
