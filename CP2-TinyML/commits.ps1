# Executar localmente após revisão: powershell -File .\CP2-TinyML\commits.ps1
$ErrorActionPreference='Stop'
$repoCp2=Split-Path -Parent $PSScriptRoot
function GitCp2 { & git -C $repoCp2 @args; if($LASTEXITCODE -ne 0){throw 'Git falhou; parar e revisar estado.'} }
GitCp2 rev-parse --show-toplevel
$stagedCp2=& git -C $repoCp2 diff --cached --name-only
if($LASTEXITCODE -ne 0){throw 'Não foi possível verificar índice.'}
if($stagedCp2){throw 'Índice contém alterações prévias. Revisar antes de continuar.'}
GitCp2 add -- CP2-TinyML/coleta CP2-TinyML/.gitignore
GitCp2 commit -m 'feat(cp2): preparar coleta HC-SR04 com confirmação de GPIOs'
GitCp2 add -- CP2-TinyML/dataset
GitCp2 commit -m 'data(cp2): validar dataset sintético e separar janelas sem sobreposição'
GitCp2 add -- CP2-TinyML/edge-impulse CP2-TinyML/modelo
GitCp2 commit -m 'docs(cp2): documentar configuração e treinamento pendentes no Edge Impulse'
GitCp2 add -- CP2-TinyML/software
GitCp2 commit -m 'feat(cp2): preparar integração TinyML e parada por falhas no carrinho'
GitCp2 add -- CP2-TinyML/testes CP2-TinyML/evidencias CP2-TinyML/README.md CP2-TinyML/commits.ps1
GitCp2 commit -m 'test(cp2): registrar validação de dados e roteiro físico pendente'
GitCp2 status --short
