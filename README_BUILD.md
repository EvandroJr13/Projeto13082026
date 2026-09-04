Instruções para gerar .exe (Windows)

1) Pré-requisitos
- Python 3.8+ instalado e no PATH.
- Conexão com a internet para instalar dependências.

2) Procedimento automático
- Execute build_exe.bat (duplo clique). O script irá:
  - Atualizar pip
  - Instalar PyInstaller
  - Instalar dependências (requirements.txt) ou customtkinter
  - Gerar um .exe em modo onefile e salvar em: %USERPROFILE%\Desktop

3) Observações
- Se preferir usar um ambiente virtual, ative-o antes de executar o script.
- Para incluir um ícone, adicione o argumento: --icon seu_icone.ico ao comando pyinstaller.
- Alguns antivírus podem sinalizar executáveis gerados localmente; assine/assinatura digital se necessário.

Comandos manuais equivalentes (caso prefira):

```bat
python -m pip install pyinstaller
pyinstaller --onefile --windowed --name Projeto13082026 Projeto13082026.py --distpath "%USERPROFILE%\\Desktop"
```

Fim.
