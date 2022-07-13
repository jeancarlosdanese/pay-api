# API Pay - API para registro de recebíveis

## Sobre ou porquê do projeto

A ideia deste projeto surgiu da necessidade de emitir boletos do Banco do Brasil através da API disponibilizada pelo banco, mas por que não desenvolver diretamente pela plataforma disponibilizada pelo banco?

Porque precisamos de um microsserviço que atenda outros sistemas da nossa empresa e gostaríamos de facilitar a implementação nesses outros sistemas, além de facilitar a manutenção e implementação de novas funcionalidades em um só lugar.
Além disso, a API do BB não gera o PDF do boleto, algo que fará parte deste projeto.

## Funções e Implementações

### Registrar boleto no banco

- [x] Registrar boleto banário no banco
- [ ] Listar boletos emitidos
- [ ] Consultar boletos por id
- [ ] Alterar boleto por id
- [ ] Baixar boleto
