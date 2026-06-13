"""Testes da camada kairos/platform/ e dos pontos de integração.

Cobertura obrigatória:
- ConfigPathBackend: paths corretos por plataforma
- NotificationBackend: no-op em ausência de ferramentas, sem raise
- MusicBackend: available=False fora do Linux
- LauncherBackend: no-op fora do Linux
- Bug fix yt-dlp: RuntimeError PT-BR quando ausente
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch


# ── PASSO 2.1 — ConfigPathBackend ─────────────────────────────────────────

class TestConfigPaths(unittest.TestCase):

    def test_linux_config_dir(self):
        with patch.object(sys, "platform", "linux"):
            from kairos.platform import paths
            import importlib
            importlib.reload(paths)
            result = paths.config_dir()
            self.assertTrue(str(result).endswith("/.config/kairos"),
                msg=f"Linux config_dir errado: {result}")

    def test_windows_config_dir(self):
        with patch.object(sys, "platform", "win32"):
            from kairos.platform import paths
            import importlib
            importlib.reload(paths)
            result = paths.config_dir()
            self.assertIn("AppData", str(result),
                msg=f"Windows config_dir deve conter AppData: {result}")
            self.assertIn("kairos", str(result))

    def test_macos_config_dir(self):
        with patch.object(sys, "platform", "darwin"):
            from kairos.platform import paths
            import importlib
            importlib.reload(paths)
            result = paths.config_dir()
            self.assertTrue(str(result).endswith("/.config/kairos"),
                msg=f"macOS config_dir errado: {result}")

    def test_linux_notebooklm_dir(self):
        with patch.object(sys, "platform", "linux"):
            from kairos.platform import paths
            import importlib
            importlib.reload(paths)
            result = paths.notebooklm_dir()
            self.assertTrue(str(result).endswith("/.notebooklm"),
                msg=f"Linux notebooklm_dir errado: {result}")

    def test_windows_notebooklm_dir(self):
        with patch.object(sys, "platform", "win32"):
            from kairos.platform import paths
            import importlib
            importlib.reload(paths)
            result = paths.notebooklm_dir()
            self.assertIn("AppData", str(result),
                msg=f"Windows notebooklm_dir deve conter AppData: {result}")

    def test_config_path_uses_config_dir(self):
        """config.py não pode ter Path.home() / '.config' hardcoded."""
        with open("kairos/config/config.py") as f:
            src = f.read()
        self.assertNotIn('Path.home() / ".config"', src,
            msg="config.py ainda usa Path.home() / '.config' hardcoded")
        self.assertIn("config_dir()", src,
            msg="config.py não usa config_dir()")

    def test_defaults_notebooklm_home_empty(self):
        """defaults.py deve ter notebooklm_home como string vazia."""
        from kairos.config.defaults import DEFAULT_CONFIG
        val = DEFAULT_CONFIG.get("notebooklm_home", "AUSENTE")
        self.assertEqual(val, "",
            msg=f"notebooklm_home deve ser '' mas é '{val}'")


# ── PASSO 2.2 — NotificationBackend ───────────────────────────────────────

class TestNotifications(unittest.TestCase):

    def test_notify_no_raise_without_tools(self):
        """notify() nunca levanta exceção, mesmo sem ferramentas."""
        with patch("shutil.which", return_value=None):
            from kairos.platform import notifications
            try:
                notifications.notify("Título", "Corpo")
            except Exception as e:
                self.fail(f"notify() levantou {type(e).__name__}: {e}")

    def test_notify_linux_calls_notify_send(self):
        fake_exe = "/usr/bin/notify-send"
        with patch.object(sys, "platform", "linux"), \
             patch("shutil.which", return_value=fake_exe), \
             patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            from kairos.platform import notifications
            import importlib
            importlib.reload(notifications)
            notifications.notify("T", "B")
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            self.assertIn("notify-send", args[0])

    def test_notify_windows_no_raise(self):
        # Importa o módulo ANTES de envenenar __import__ — patchar __import__
        # global quebraria a própria linha `from ... import` (não é o alvo do
        # teste). Alvo real: plyer/ctypes ausentes DENTRO de _notify_windows.
        from kairos.platform import notifications
        import importlib
        importlib.reload(notifications)
        with patch.object(sys, "platform", "win32"), \
             patch("builtins.__import__", side_effect=ImportError):
            try:
                notifications._notify_windows("T", "B")
            except Exception as e:
                self.fail(f"_notify_windows levantou {type(e).__name__}: {e}")

    def test_notify_macos_no_raise_without_osascript(self):
        with patch.object(sys, "platform", "darwin"), \
             patch("shutil.which", return_value=None):
            from kairos.platform import notifications
            import importlib
            importlib.reload(notifications)
            try:
                notifications._notify_macos("T", "B")
            except Exception as e:
                self.fail(f"_notify_macos levantou {type(e).__name__}: {e}")

    def test_notifier_re_exports_notify(self):
        """notifier.py deve re-exportar notify de platform.notifications."""
        from kairos.integrations import notifier
        self.assertTrue(callable(getattr(notifier, "notify", None)),
            msg="notifier.notify não é callable após refactor")


# ── PASSO 2.3 — MusicBackend ──────────────────────────────────────────────

class TestMusicBackend(unittest.TestCase):

    def test_is_supported_false_on_windows(self):
        with patch.object(sys, "platform", "win32"):
            from kairos.platform import music
            import importlib
            importlib.reload(music)
            self.assertFalse(music.is_supported())

    def test_is_supported_false_on_macos(self):
        with patch.object(sys, "platform", "darwin"):
            from kairos.platform import music
            import importlib
            importlib.reload(music)
            self.assertFalse(music.is_supported())

    def test_is_supported_false_on_linux_without_playerctl(self):
        with patch.object(sys, "platform", "linux"), \
             patch("shutil.which", return_value=None):
            from kairos.platform import music
            import importlib
            importlib.reload(music)
            self.assertFalse(music.is_supported())

    def test_empty_snapshot_structure(self):
        from kairos.platform.music import empty_snapshot
        snap = empty_snapshot()
        required = {"status", "title", "artist", "artUrl", "canNext", "canPrev", "available"}
        self.assertEqual(required, set(snap.keys()),
            msg=f"empty_snapshot keys incorretas: {set(snap.keys())}")
        self.assertFalse(snap["available"])

    def test_snapshot_returns_empty_on_unsupported_platform(self):
        with patch.object(sys, "platform", "win32"), \
             patch("kairos.platform.music.is_supported", return_value=False):
            from kairos.integrations import music_mpris
            result = music_mpris.snapshot()
            self.assertFalse(result["available"],
                msg="snapshot() deve retornar available=False fora do Linux")

    def test_snapshot_no_subprocess_on_unsupported(self):
        """snapshot() não deve invocar subprocess fora do Linux."""
        with patch.object(sys, "platform", "win32"), \
             patch("kairos.platform.music.is_supported", return_value=False), \
             patch("subprocess.run") as mock_run:
            from kairos.integrations import music_mpris
            music_mpris.snapshot()
            mock_run.assert_not_called()


# ── PASSO 2.4 — LauncherBackend ───────────────────────────────────────────

class TestLauncherBackend(unittest.TestCase):

    def test_start_noop_on_windows(self):
        with patch.object(sys, "platform", "win32"), \
             patch("subprocess.Popen") as mock_popen:
            from kairos.integrations import launcher
            import importlib
            importlib.reload(launcher)
            launcher.start()
            mock_popen.assert_not_called()

    def test_start_noop_on_macos(self):
        with patch.object(sys, "platform", "darwin"), \
             patch("subprocess.Popen") as mock_popen:
            from kairos.integrations import launcher
            import importlib
            importlib.reload(launcher)
            launcher.start()
            mock_popen.assert_not_called()

    def test_hyprland_rules_only_on_linux(self):
        """_setup_background_rules não deve rodar fora do Linux."""
        with patch.object(sys, "platform", "win32"), \
             patch("subprocess.run") as mock_run:
            from kairos.integrations import launcher
            launcher._setup_background_rules()
            mock_run.assert_not_called()

    def test_cold_start_omits_playlist_arg(self):
        """Launch em 2 fases: cold start NÃO leva a playlist como argumento
        (evita corrida do deep-link); a entrega é agendada em thread separada."""
        from kairos.integrations import launcher
        import importlib
        importlib.reload(launcher)
        fake_cfg = {
            "simpmusic_autostart": True,
            "simpmusic_path": "/usr/bin/simpmusic",
            "music_playlist_url": "https://x/playlist",
        }
        with patch.object(sys, "platform", "linux"), \
             patch.object(launcher.cfg, "load", return_value=fake_cfg), \
             patch.object(launcher, "_already_running", return_value=False), \
             patch.object(launcher, "_setup_background_rules"), \
             patch("pathlib.Path.exists", return_value=True), \
             patch("threading.Thread") as mock_thread, \
             patch("subprocess.Popen") as mock_popen:
            mock_popen.return_value = MagicMock(pid=123)
            launcher.start()
            cmd = mock_popen.call_args[0][0]
            self.assertEqual(cmd, ["/usr/bin/simpmusic"],
                msg=f"cold start não deve levar a playlist como arg: {cmd}")
            mock_thread.assert_called_once()

    def test_deliver_playlist_second_invocation_when_ready(self):
        """_deliver_playlist entrega a URL via 2ª invocação quando o player
        já registrou no MPRIS."""
        from kairos.integrations import launcher
        with patch.object(launcher, "_already_running", return_value=True), \
             patch("subprocess.run") as mock_run:
            launcher._deliver_playlist(Path("/usr/bin/simpmusic"), "https://x/pl")
            mock_run.assert_called_once()
            self.assertEqual(mock_run.call_args[0][0],
                ["/usr/bin/simpmusic", "https://x/pl"])

    def test_deliver_playlist_noop_on_timeout(self):
        """_deliver_playlist não invoca nada se o player nunca registrar."""
        from kairos.integrations import launcher
        with patch.object(launcher, "_already_running", return_value=False), \
             patch.object(launcher, "_DELIVER_TIMEOUT_S", 0.0), \
             patch("subprocess.run") as mock_run:
            launcher._deliver_playlist(Path("/usr/bin/simpmusic"), "https://x")
            mock_run.assert_not_called()


# ── PASSO 2.5 — Bug fix yt-dlp ────────────────────────────────────────────

class TestYtDlpFix(unittest.TestCase):

    def test_raises_runtime_error_ptbr_when_ytdlp_missing(self):
        """Bug confirmado: antes lançava FileNotFoundError, agora deve ser RuntimeError PT-BR."""
        import tempfile
        with patch("shutil.which", return_value=None):
            from kairos.pipeline import youtube_extractor
            with self.assertRaises(RuntimeError) as ctx:
                with tempfile.TemporaryDirectory() as tmp:
                    youtube_extractor._download_audio("https://youtu.be/test", Path(tmp))
            msg = str(ctx.exception)
            self.assertIn("yt-dlp", msg,
                msg=f"RuntimeError deve mencionar yt-dlp: '{msg}'")
            # Mensagem deve ser legível em PT-BR (sem stacktrace cru)
            self.assertNotIn("FileNotFoundError", msg)

    def test_no_file_not_found_error(self):
        """FileNotFoundError não deve vazar para o usuário."""
        import tempfile
        with patch("shutil.which", return_value=None):
            from kairos.pipeline import youtube_extractor
            with self.assertRaises(RuntimeError):
                with tempfile.TemporaryDirectory() as tmp:
                    youtube_extractor._download_audio("https://youtu.be/test", Path(tmp))


# ── PASSO 2.6 — Regressão: comportamentos existentes preservados ──────────

class TestRegressions(unittest.TestCase):

    def test_config_load_returns_dict(self):
        from kairos.config import config
        result = config.load()
        self.assertIsInstance(result, dict)
        self.assertIn("obsidian_vault_path", result)

    def test_config_save_load_roundtrip(self):
        import json
        import tempfile
        from kairos.config import config
        original = config._CONFIG_PATH
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            json.dump({}, f)
            tmp_path = Path(f.name)
        try:
            config._CONFIG_PATH = tmp_path
            config.save({"obsidian_vault_path": "/tmp/vault"})
            loaded = config.load()
            self.assertEqual(loaded["obsidian_vault_path"], "/tmp/vault")
        finally:
            config._CONFIG_PATH = original
            tmp_path.unlink(missing_ok=True)

    def test_ingestor_raises_value_error_on_unknown_type(self):
        from kairos.pipeline.ingestor import ingest
        with self.assertRaises(ValueError):
            ingest("/tmp/arquivo.xyz_desconhecido")

    def test_format_duration_zero(self):
        from kairos.util import format_duration
        self.assertEqual(format_duration(0), "0m00s")

    def test_format_duration_negative(self):
        from kairos.util import format_duration
        self.assertEqual(format_duration(-5), "0m00s")

    def test_format_duration_normal(self):
        from kairos.util import format_duration
        self.assertEqual(format_duration(134), "2m14s")

    def test_truncate_at_line_no_truncation_needed(self):
        from kairos.util import truncate_at_line
        text = "linha1\nlinha2\nlinha3"
        result = truncate_at_line(text, 9999, "[truncado]")
        self.assertEqual(result, text)

    def test_notebooklm_client_defers_storage_path_to_lib(self):
        """client deve usar notebooklm.paths.get_storage_path, não remontar
        profiles/default/storage_state.json à mão (DEC-014)."""
        with open("kairos/integrations/notebooklm_client.py") as f:
            src = f.read()
        self.assertIn("get_storage_path", src,
            msg="client não defere a notebooklm.paths.get_storage_path")
        self.assertNotIn('"profiles" / "default"', src,
            msg="client ainda remonta o caminho profiles/default à mão")

    def test_platform_import_does_not_import_config(self):
        """platform/paths.py não pode importar de kairos.config — circular."""
        with open("kairos/platform/paths.py") as f:
            src = f.read()
        self.assertNotIn("from kairos.config", src,
            msg="paths.py importa kairos.config — import circular!")
        self.assertNotIn("import kairos.config", src,
            msg="paths.py importa kairos.config — import circular!")


if __name__ == "__main__":
    unittest.main(verbosity=2)
