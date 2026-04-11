from __future__ import annotations

import argparse
import json
import os
import sys
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import messagebox, ttk


BASE_DIR = Path(__file__).resolve().parent
STATE_FILE = BASE_DIR / "launcher_state.json"
INSTALLS_DIR = BASE_DIR / "installed_games"

BG = "#0a0d14"
PANEL = "#111827"
PANEL_ALT = "#0f1725"
CARD = "#151d2d"
CARD_ACTIVE = "#1d2940"
TEXT = "#eef2ff"
MUTED = "#90a0bb"
ACCENT = "#4ea1ff"
ACCENT_SOFT = "#203a63"
SUCCESS = "#47d18c"
WARNING = "#ffb84d"


@dataclass(frozen=True)
class Game:
	game_id: str
	title: str
	genre: str
	description: str
	version: str
	accent: str


GAMES = [
	Game(
		game_id="phantom_protocol",
		title="Phantom Protocol",
		genre="Action RPG",
		description="Taktyczna kampania z dynamicznymi misjami i sezonowymi aktualizacjami.",
		version="2.8.1",
		accent="#4ea1ff",
	),
	Game(
		game_id="solar_drift",
		title="Solar Drift",
		genre="Sci-Fi Racing",
		description="Wyścigi między orbitalnymi torami z rankingiem online i turniejami.",
		version="1.4.3",
		accent="#ff7a59",
	),
	Game(
		game_id="citadel_zero",
		title="Citadel Zero",
		genre="Strategy",
		description="Dowodzenie frakcją, budowa bazy i wielkie bitwy PvE oraz PvP.",
		version="5.0.0",
		accent="#7c5cff",
	),
]


def resource_path(name: str) -> Path:
	root = Path(getattr(sys, "_MEIPASS", BASE_DIR))
	return root / name


class LauncherApp(tk.Tk):
	def __init__(self) -> None:
		super().__init__()
		self.title("Negro Games Launcher")
		self.geometry("1360x860")
		self.minsize(1180, 760)
		self.configure(bg=BG)

		self.games = {game.game_id: game for game in GAMES}
		self.selected_game_id = GAMES[0].game_id
		self.installed_games = self._load_state()
		self.download_job: str | None = None
		self.download_progress = 0
		self.download_target: str | None = None
		self.card_widgets: dict[str, tk.Frame] = {}
		self.card_status_labels: dict[str, tk.Label] = {}
		self.card_action_buttons: dict[str, tk.Button] = {}

		self._setup_styles()
		self._load_logo()
		self._build_ui()
		self._refresh_all()

	def _setup_styles(self) -> None:
		style = ttk.Style(self)
		style.theme_use("clam")
		style.configure(
			"Launcher.Horizontal.TProgressbar",
			troughcolor="#1a2436",
			background=ACCENT,
			bordercolor="#1a2436",
			lightcolor=ACCENT,
			darkcolor=ACCENT,
			thickness=12,
		)

	def _load_logo(self) -> None:
		self.logo_image = None
		logo_path = resource_path("logo.png")
		if logo_path.exists():
			try:
				self.logo_image = tk.PhotoImage(file=str(logo_path))
				self.iconphoto(True, self.logo_image)
			except tk.TclError:
				self.logo_image = None

	def _build_ui(self) -> None:
		shell = tk.Frame(self, bg=BG)
		shell.pack(fill="both", expand=True, padx=24, pady=24)
		shell.grid_columnconfigure(1, weight=1)
		shell.grid_rowconfigure(0, weight=1)

		sidebar = tk.Frame(shell, bg=PANEL, width=230, highlightthickness=1, highlightbackground="#1a2436")
		sidebar.grid(row=0, column=0, sticky="nsw")
		sidebar.grid_propagate(False)

		main_area = tk.Frame(shell, bg=BG)
		main_area.grid(row=0, column=1, sticky="nsew", padx=(20, 0))
		main_area.grid_columnconfigure(0, weight=1)
		main_area.grid_rowconfigure(1, weight=1)

		self._build_sidebar(sidebar)
		self._build_header(main_area)
		self._build_content(main_area)
		self._build_footer(main_area)

	def _build_sidebar(self, parent: tk.Frame) -> None:
		brand = tk.Frame(parent, bg=PANEL)
		brand.pack(fill="x", padx=20, pady=(22, 10))

		if self.logo_image is not None:
			logo_label = tk.Label(brand, image=self.logo_image, bg=PANEL)
			logo_label.pack(anchor="w")

		tk.Label(
			brand,
			text="NEGRO GAMES",
			bg=PANEL,
			fg=TEXT,
			font=("Segoe UI Semibold", 20),
		).pack(anchor="w", pady=(10, 2))
		tk.Label(
			brand,
			text="Launcher Desktop",
			bg=PANEL,
			fg=MUTED,
			font=("Segoe UI", 10),
		).pack(anchor="w")

		nav = tk.Frame(parent, bg=PANEL)
		nav.pack(fill="x", padx=12, pady=(16, 0))

		for label in ("Discover", "Library", "Downloads", "Settings"):
			button = tk.Button(
				nav,
				text=label,
				anchor="w",
				relief="flat",
				bd=0,
				bg=PANEL,
				fg=TEXT if label == "Library" else MUTED,
				activebackground=CARD_ACTIVE,
				activeforeground=TEXT,
				font=("Segoe UI Semibold", 12),
				padx=16,
				pady=12,
				cursor="hand2",
				command=lambda item=label: self._set_status(f"Sekcja {item} jest przygotowana w tym widoku launchera."),
			)
			button.pack(fill="x", pady=4)

		stats = tk.Frame(parent, bg=PANEL_ALT, highlightthickness=1, highlightbackground="#1a2436")
		stats.pack(fill="x", padx=16, pady=(24, 0))

		tk.Label(stats, text="Aktywne konto", bg=PANEL_ALT, fg=MUTED, font=("Segoe UI", 10)).pack(anchor="w", padx=14, pady=(14, 2))
		tk.Label(stats, text="negrogames.dev", bg=PANEL_ALT, fg=TEXT, font=("Segoe UI Semibold", 12)).pack(anchor="w", padx=14)
		tk.Label(stats, text="3 gry w bibliotece", bg=PANEL_ALT, fg=MUTED, font=("Segoe UI", 10)).pack(anchor="w", padx=14, pady=(4, 14))

		self.sidebar_progress = tk.Label(
			parent,
			text="Brak aktywnego pobierania",
			bg=PANEL,
			fg=MUTED,
			font=("Segoe UI", 10),
			wraplength=180,
			justify="left",
		)
		self.sidebar_progress.pack(anchor="w", padx=20, pady=(24, 0))

	def _build_header(self, parent: tk.Frame) -> None:
		header = tk.Frame(parent, bg=BG)
		header.grid(row=0, column=0, sticky="ew", pady=(0, 18))
		header.grid_columnconfigure(0, weight=1)

		copy = tk.Frame(header, bg=BG)
		copy.grid(row=0, column=0, sticky="w")

		tk.Label(copy, text="Nowy launcher", bg=BG, fg=ACCENT, font=("Segoe UI Semibold", 12)).pack(anchor="w")
		tk.Label(copy, text="Biblioteka jak w aplikacji sklepu", bg=BG, fg=TEXT, font=("Segoe UI Semibold", 28)).pack(anchor="w", pady=(6, 4))
		tk.Label(
			copy,
			text="Desktopowy launcher do instalowania, aktualizowania i uruchamiania gier z jednego miejsca.",
			bg=BG,
			fg=MUTED,
			font=("Segoe UI", 11),
		).pack(anchor="w")

	def _build_content(self, parent: tk.Frame) -> None:
		content = tk.Frame(parent, bg=BG)
		content.grid(row=1, column=0, sticky="nsew")
		content.grid_columnconfigure(0, weight=3)
		content.grid_columnconfigure(1, weight=2)
		content.grid_rowconfigure(1, weight=1)

		hero = tk.Frame(content, bg=PANEL_ALT, highlightthickness=1, highlightbackground="#1a2436")
		hero.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 18))
		hero.grid_columnconfigure(0, weight=1)
		hero.grid_columnconfigure(1, weight=1)

		hero_copy = tk.Frame(hero, bg=PANEL_ALT)
		hero_copy.grid(row=0, column=0, sticky="nsew", padx=28, pady=28)

		tk.Label(hero_copy, text="Wyróżniona gra", bg=PANEL_ALT, fg=ACCENT, font=("Segoe UI Semibold", 11)).pack(anchor="w")
		self.hero_title = tk.Label(hero_copy, bg=PANEL_ALT, fg=TEXT, font=("Segoe UI Semibold", 30))
		self.hero_title.pack(anchor="w", pady=(8, 8))
		self.hero_description = tk.Label(hero_copy, bg=PANEL_ALT, fg=MUTED, font=("Segoe UI", 11), justify="left", wraplength=520)
		self.hero_description.pack(anchor="w")

		hero_actions = tk.Frame(hero_copy, bg=PANEL_ALT)
		hero_actions.pack(anchor="w", pady=(22, 0))

		self.install_button = tk.Button(
			hero_actions,
			text="Zainstaluj",
			command=self.install_selected_game,
			relief="flat",
			bd=0,
			bg=ACCENT,
			fg="#06101d",
			activebackground="#76b8ff",
			activeforeground="#06101d",
			font=("Segoe UI Semibold", 12),
			padx=20,
			pady=11,
			cursor="hand2",
		)
		self.install_button.pack(side="left")

		self.launch_button = tk.Button(
			hero_actions,
			text="Uruchom",
			command=self.launch_selected_game,
			relief="flat",
			bd=0,
			bg=ACCENT_SOFT,
			fg=TEXT,
			activebackground="#2d4c7a",
			activeforeground=TEXT,
			font=("Segoe UI Semibold", 12),
			padx=20,
			pady=11,
			cursor="hand2",
		)
		self.launch_button.pack(side="left", padx=(12, 0))

		self.hero_meta = tk.Label(hero_copy, bg=PANEL_ALT, fg=MUTED, font=("Segoe UI", 10))
		self.hero_meta.pack(anchor="w", pady=(16, 0))

		visual = tk.Canvas(hero, bg="#0b1120", height=240, highlightthickness=0)
		visual.grid(row=0, column=1, sticky="nsew")
		visual.create_rectangle(24, 24, 360, 216, fill="#101a2e", outline="")
		visual.create_rectangle(46, 48, 338, 192, fill="#13233a", outline="")
		visual.create_text(70, 78, text="NEGRO GAMES", anchor="w", fill=TEXT, font=("Segoe UI Semibold", 18))
		visual.create_text(70, 116, text="Launcher Desktop", anchor="w", fill=ACCENT, font=("Segoe UI", 24))
		visual.create_text(70, 154, text="Install  Update  Launch", anchor="w", fill=MUTED, font=("Segoe UI", 12))
		visual.create_rectangle(70, 178, 196, 188, fill=ACCENT, outline="")

		library = tk.Frame(content, bg=BG)
		library.grid(row=1, column=0, sticky="nsew", padx=(0, 18))

		tk.Label(library, text="Biblioteka", bg=BG, fg=TEXT, font=("Segoe UI Semibold", 20)).pack(anchor="w")
		tk.Label(library, text="Kliknij kartę gry, aby zmienić aktywny widok launchera.", bg=BG, fg=MUTED, font=("Segoe UI", 10)).pack(anchor="w", pady=(4, 14))

		cards = tk.Frame(library, bg=BG)
		cards.pack(fill="both", expand=True)
		cards.grid_columnconfigure((0, 1), weight=1)

		for index, game in enumerate(GAMES):
			card = tk.Frame(cards, bg=CARD, highlightthickness=1, highlightbackground="#1a2436", padx=18, pady=18, cursor="hand2")
			row = index // 2
			column = index % 2
			card.grid(row=row, column=column, sticky="nsew", padx=(0, 14) if column == 0 else 0, pady=(0, 14))
			card.grid_columnconfigure(0, weight=1)

			accent_bar = tk.Frame(card, bg=game.accent, height=6)
			accent_bar.grid(row=0, column=0, sticky="ew", pady=(0, 14))

			title = tk.Label(card, text=game.title, bg=CARD, fg=TEXT, font=("Segoe UI Semibold", 18), cursor="hand2")
			title.grid(row=1, column=0, sticky="w")

			genre = tk.Label(card, text=game.genre, bg=CARD, fg=MUTED, font=("Segoe UI", 10), cursor="hand2")
			genre.grid(row=2, column=0, sticky="w", pady=(4, 10))

			description = tk.Label(card, text=game.description, bg=CARD, fg="#c2cce0", font=("Segoe UI", 10), justify="left", wraplength=360, cursor="hand2")
			description.grid(row=3, column=0, sticky="w")

			status = tk.Label(card, bg=CARD, fg=MUTED, font=("Segoe UI Semibold", 10), cursor="hand2")
			status.grid(row=4, column=0, sticky="w", pady=(16, 10))

			action = tk.Button(
				card,
				relief="flat",
				bd=0,
				bg=ACCENT_SOFT,
				fg=TEXT,
				activebackground="#2d4c7a",
				activeforeground=TEXT,
				font=("Segoe UI Semibold", 10),
				padx=14,
				pady=9,
				cursor="hand2",
				command=lambda game_id=game.game_id: self.toggle_game_install(game_id),
			)
			action.grid(row=5, column=0, sticky="w")

			for widget in (card, title, genre, description, status, accent_bar):
				widget.bind("<Button-1>", lambda _event, game_id=game.game_id: self.select_game(game_id))

			self.card_widgets[game.game_id] = card
			self.card_status_labels[game.game_id] = status
			self.card_action_buttons[game.game_id] = action

		queue = tk.Frame(content, bg=PANEL, highlightthickness=1, highlightbackground="#1a2436")
		queue.grid(row=1, column=1, sticky="nsew")
		queue.grid_columnconfigure(0, weight=1)

		tk.Label(queue, text="Pobieranie", bg=PANEL, fg=TEXT, font=("Segoe UI Semibold", 20)).grid(row=0, column=0, sticky="w", padx=20, pady=(20, 6))
		tk.Label(queue, text="Aktywna kolejka launchera", bg=PANEL, fg=MUTED, font=("Segoe UI", 10)).grid(row=1, column=0, sticky="w", padx=20)

		self.download_title = tk.Label(queue, text="Brak aktywnego zadania", bg=PANEL, fg=TEXT, font=("Segoe UI Semibold", 16))
		self.download_title.grid(row=2, column=0, sticky="w", padx=20, pady=(22, 6))

		self.download_details = tk.Label(queue, text="Wybierz grę i kliknij Zainstaluj.", bg=PANEL, fg=MUTED, font=("Segoe UI", 10), justify="left", wraplength=320)
		self.download_details.grid(row=3, column=0, sticky="w", padx=20)

		self.progress_value = tk.StringVar(value="0%")
		self.progressbar = ttk.Progressbar(queue, style="Launcher.Horizontal.TProgressbar", mode="determinate", maximum=100)
		self.progressbar.grid(row=4, column=0, sticky="ew", padx=20, pady=(20, 8))

		tk.Label(queue, textvariable=self.progress_value, bg=PANEL, fg=TEXT, font=("Segoe UI Semibold", 12)).grid(row=5, column=0, sticky="w", padx=20)

		info = tk.Frame(queue, bg=PANEL_ALT)
		info.grid(row=6, column=0, sticky="ew", padx=20, pady=(22, 20))
		tk.Label(info, text="Status launchera", bg=PANEL_ALT, fg=MUTED, font=("Segoe UI", 10)).pack(anchor="w", padx=14, pady=(14, 4))
		self.status_text = tk.Label(info, text="Launcher gotowy.", bg=PANEL_ALT, fg=TEXT, font=("Segoe UI", 11), justify="left", wraplength=320)
		self.status_text.pack(anchor="w", padx=14, pady=(0, 14))

	def _build_footer(self, parent: tk.Frame) -> None:
		footer = tk.Frame(parent, bg=BG)
		footer.grid(row=2, column=0, sticky="ew", pady=(18, 0))

		self.footer_label = tk.Label(
			footer,
			text="Launcher gotowy do pracy.",
			bg=BG,
			fg=MUTED,
			font=("Segoe UI", 10),
		)
		self.footer_label.pack(anchor="w")

	def _load_state(self) -> set[str]:
		if not STATE_FILE.exists():
			return set()

		try:
			payload = json.loads(STATE_FILE.read_text(encoding="utf-8"))
		except (OSError, json.JSONDecodeError):
			return set()

		installed = payload.get("installed_games", [])
		return {game_id for game_id in installed if game_id in self.games}

	def _save_state(self) -> None:
		payload = {"installed_games": sorted(self.installed_games)}
		STATE_FILE.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")

	def _set_status(self, text: str) -> None:
		self.status_text.configure(text=text)
		self.footer_label.configure(text=text)

	def select_game(self, game_id: str) -> None:
		self.selected_game_id = game_id
		self._refresh_all()
		self._set_status(f"Wybrano {self.games[game_id].title}.")

	def _refresh_all(self) -> None:
		self._refresh_hero()
		self._refresh_cards()
		self._refresh_download_panel()

	def _refresh_hero(self) -> None:
		game = self.games[self.selected_game_id]
		installed = self.selected_game_id in self.installed_games

		self.hero_title.configure(text=game.title)
		self.hero_description.configure(text=game.description)
		state_text = "Zainstalowana" if installed else "Gotowa do instalacji"
		self.hero_meta.configure(text=f"{game.genre}   Version {game.version}   {state_text}")

		self.install_button.configure(text="Aktualizuj" if installed else "Zainstaluj")
		self.launch_button.configure(state="normal" if installed else "disabled")

	def _refresh_cards(self) -> None:
		for game_id, card in self.card_widgets.items():
			selected = game_id == self.selected_game_id
			installed = game_id in self.installed_games
			card.configure(bg=CARD_ACTIVE if selected else CARD)

			for child in card.winfo_children():
				if isinstance(child, tk.Frame):
					continue
				child.configure(bg=CARD_ACTIVE if selected else CARD)

			status = "Zainstalowana" if installed else "Nie zainstalowano"
			status_color = SUCCESS if installed else WARNING
			self.card_status_labels[game_id].configure(text=status, fg=status_color)

			button = self.card_action_buttons[game_id]
			button.configure(text="Uruchom" if installed else "Zainstaluj")

	def _refresh_download_panel(self) -> None:
		if self.download_target is None:
			self.download_title.configure(text="Brak aktywnego zadania")
			self.download_details.configure(text="Wybierz grę i kliknij Zainstaluj.")
			self.sidebar_progress.configure(text="Brak aktywnego pobierania")
			self.progressbar.configure(value=0)
			self.progress_value.set("0%")
			return

		game = self.games[self.download_target]
		self.download_title.configure(text=game.title)
		self.download_details.configure(text="Launcher pobiera pliki gry i przygotowuje lokalną instalację.")
		self.sidebar_progress.configure(text=f"Pobieranie: {game.title}\n{self.download_progress}%")
		self.progressbar.configure(value=self.download_progress)
		self.progress_value.set(f"{self.download_progress}%")

	def toggle_game_install(self, game_id: str) -> None:
		self.select_game(game_id)
		if game_id in self.installed_games:
			self.launch_selected_game()
			return

		self.install_selected_game()

	def install_selected_game(self) -> None:
		if self.download_job is not None:
			self._set_status("Poczekaj, az aktualne pobieranie zostanie zakonczone.")
			return

		self.download_target = self.selected_game_id
		self.download_progress = 0
		self.install_button.configure(state="disabled")
		self.launch_button.configure(state="disabled")
		self._refresh_download_panel()
		self._set_status(f"Rozpoczeto instalacje gry {self.games[self.selected_game_id].title}.")
		self._download_step()

	def _download_step(self) -> None:
		if self.download_target is None:
			return

		self.download_progress = min(self.download_progress + 8, 100)
		self._refresh_download_panel()

		if self.download_progress >= 100:
			self._finish_installation()
			return

		self.download_job = self.after(180, self._download_step)

	def _finish_installation(self) -> None:
		if self.download_target is None:
			return

		game_id = self.download_target
		game = self.games[game_id]
		INSTALLS_DIR.mkdir(parents=True, exist_ok=True)
		game_dir = INSTALLS_DIR / game_id
		game_dir.mkdir(parents=True, exist_ok=True)

		launcher_stub = game_dir / "launch_game.cmd"
		launcher_stub.write_text(
			"@echo off\n"
			f"title {game.title}\n"
			f"echo Launching {game.title}...\n"
			"echo This is a placeholder game process created by the launcher.\n"
			"pause\n",
			encoding="utf-8",
		)

		self.installed_games.add(game_id)
		self._save_state()
		self.download_target = None
		self.download_job = None
		self.download_progress = 0
		self.install_button.configure(state="normal")
		self.launch_button.configure(state="normal")
		self._refresh_all()
		self._set_status(f"Instalacja zakonczona. {game.title} jest gotowa do uruchomienia.")

	def launch_selected_game(self) -> None:
		game = self.games[self.selected_game_id]
		if self.selected_game_id not in self.installed_games:
			self._set_status(f"Najpierw zainstaluj {game.title}.")
			return

		launcher_path = INSTALLS_DIR / self.selected_game_id / "launch_game.cmd"
		if launcher_path.exists():
			os.startfile(str(launcher_path))
			self._set_status(f"Uruchomiono {game.title}.")
			return

		messagebox.showinfo("Launcher", f"{game.title} jest oznaczona jako zainstalowana, ale nie znaleziono pliku startowego.")


def run_smoke_test() -> None:
	app = LauncherApp()
	app.update_idletasks()
	app.update()
	app.destroy()
	print("Smoke test OK")


def main() -> None:
	parser = argparse.ArgumentParser()
	parser.add_argument("--smoke-test", action="store_true")
	args = parser.parse_args()

	if args.smoke_test:
		run_smoke_test()
		return

	app = LauncherApp()
	app.mainloop()


if __name__ == "__main__":
	main()
