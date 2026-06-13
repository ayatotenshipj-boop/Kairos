# Instrução fixa de estrutura, concatenada a TODO prompt antes de ir ao backend.
# NÃO é editável pelo usuário — é parte da arquitetura (alimenta o mapa de
# conhecimento da Fase 4). Fonte única da verdade: importada pelo processor
# (injeção) e exposta pelo backend (exibição read-only no editor de prompt).
STRUCTURE_INSTRUCTION = (
    "Formate a resposta EXATAMENTE assim, em Markdown:\n"
    "- A primeira linha é o tema principal como título nível 1: # <Tema>.\n"
    "- Em seguida, no mínimo 5 sub-temas, cada um como título nível 2 "
    "(## <Sub-tema>) seguido de 1 a 2 parágrafos que o expliquem.\n"
    "- Não escreva nada fora desse esquema (sem introdução nem conclusão soltas).\n"
    "No Obsidian, o tema vira uma pasta e cada sub-tema uma nota linkada de "
    "volta ao tema central."
)

DEFAULT_CONFIG = {
    "obsidian_vault_path": "",
    "kairos_folder": "Kairos",
    "log_filename": "study-log.md",
    "simpmusic_path": "",
    "simpmusic_autostart": True,
    "music_playlist_url": "",
    "reduce_motion": False,
    "dark_mode": True,
    "discord_presence": False,
    "discord_client_id": "",
    "notebooklm_home": "",   # resolvido em runtime por platform.paths
    "whisper_model": "small",
    "transcript_max_chars": 30000,
    "processor_max_chars": 30000,
    "processor_backend": "notebooklm",
    "gemini_api_key": "",
    "gemini_model": "gemini-flash-latest",
    "local_endpoint": "http://localhost:11434",
}
