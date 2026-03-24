from __future__ import annotations

import os
import subprocess
import sys
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox

from .config import DEFAULT_DNA_PATH, DEFAULT_RNA_PATH, ensure_output_dir
from .exporter import export_workbook_results
from .io_utils import read_dataset_sheets
from .matcher import MatchMode, build_match_column
from .profiles import DatabaseMode, load_database_table

OUTPUT_FORMULA_COLUMN_NAME = "Matched Formula"
OUTPUT_NAME_COLUMN_NAME = "Matched Short name"

COLORS = {
    "app_bg": "#F3F6FA",
    "card_bg": "#FFFFFF",
    "card_border": "#D6E0EA",
    "title": "#18324A",
    "text": "#324C63",
    "muted": "#5E7288",
    "soft_bg": "#F7FAFC",
    "input_bg": "#F8FBFD",
    "primary": "#0F766E",
    "primary_active": "#0C5D57",
    "button_text": "#FFFFFF",
    "secondary_border": "#B8C8D8",
    "secondary_bg": "#FFFFFF",
    "secondary_hover": "#EEF4F8",
    "dna": "#2563EB",
    "rna": "#DC2626",
    "warning_bg": "#FFF7E8",
    "warning_fg": "#A16207",
    "ready_bg": "#E8F7F4",
    "ready_fg": "#0F766E",
    "success_bg": "#EAF7EF",
    "success_fg": "#166534",
    "error_bg": "#FDECEC",
    "error_fg": "#B42318",
}

def _system_font() -> str:
    if sys.platform == "darwin":
        return "Helvetica Neue"
    return "Segoe UI"

_FONT = _system_font()

FONTS = {
    "title": (_FONT, 19, "bold"),
    "subtitle": (_FONT, 10),
    "card_title": (_FONT, 11, "bold"),
    "label": (_FONT, 9, "bold"),
    "text": (_FONT, 10),
    "small": (_FONT, 9),
    "button": (_FONT, 10, "bold"),
    "badge": (_FONT, 8, "bold"),
}

MODE_META = {
    MatchMode.DNA: {
        "title": "DNA",
        "subtitle": "Accept Mz, m/z, Precursor Ion m/z, Charged monoisotopic mass, [M+H]+ Protonated Mass, etc.",
    },
    MatchMode.RNA: {
        "title": "RNA",
        "subtitle": "All DNA columns plus [M+H]+",
    },
    MatchMode.BOTH: {
        "title": "Both",
        "subtitle": "DNA first, then RNA with shared mass rules",
    },
}


@dataclass
class AppState:
    dataset_path: Path | None
    dna_db_path: Path
    rna_db_path: Path
    output_dir: Path

    @classmethod
    def create(cls) -> "AppState":
        return cls(
            dataset_path=None,
            dna_db_path=DEFAULT_DNA_PATH,
            rna_db_path=DEFAULT_RNA_PATH,
            output_dir=ensure_output_dir(),
        )


def _same_path(left: Path, right: Path) -> bool:
    return left.expanduser().resolve(strict=False) == right.expanduser().resolve(strict=False)


def path_badge_text(current: Path, default: Path) -> str:
    return "Default" if _same_path(current, default) else "Custom"


def describe_mode(mode: MatchMode) -> str:
    if mode == MatchMode.DNA:
        return "Compare dataset m/z against DNA masses (Mz, m/z, Precursor Ion m/z, Charged monoisotopic mass, [M+H]+ Protonated Mass)."
    if mode == MatchMode.RNA:
        return "Compare dataset m/z against RNA masses (all DNA columns plus [M+H]+)."
    return "Run DNA first, then RNA, with the same Mz parsing rules across both databases."


def status_appearance(message: str) -> dict[str, str]:
    if message.startswith("Failed:"):
        return {
            "tone": "error",
            "title": "Attention Needed",
            "background": COLORS["error_bg"],
            "foreground": COLORS["error_fg"],
        }
    if message.startswith("Saved result to:"):
        return {
            "tone": "success",
            "title": "Export Complete",
            "background": COLORS["success_bg"],
            "foreground": COLORS["success_fg"],
        }
    return {
        "tone": "ready",
        "title": "Ready to Run",
        "background": COLORS["ready_bg"],
        "foreground": COLORS["ready_fg"],
    }


def open_output_folder(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        os.startfile(path)  # type: ignore[attr-defined]
        return
    if os.name == "posix":
        opener = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.Popen([opener, str(path)])
        return
    raise OSError(f"Unsupported platform for opening folders: {os.name}")


def run_matching(state: AppState, mode: MatchMode) -> Path:
    if state.dataset_path is None:
        raise ValueError("Please select a dataset file before running matching.")
    if not state.dataset_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {state.dataset_path}")

    dataset_sheets = read_dataset_sheets(state.dataset_path)

    dna_table = None
    rna_table = None
    if mode in (MatchMode.DNA, MatchMode.BOTH):
        dna_table = load_database_table(
            state.dna_db_path,
            DatabaseMode.DNA,
            use_default_profile=_same_path(state.dna_db_path, DEFAULT_DNA_PATH),
        )
    if mode in (MatchMode.RNA, MatchMode.BOTH):
        rna_table = load_database_table(
            state.rna_db_path,
            DatabaseMode.RNA,
            use_default_profile=_same_path(state.rna_db_path, DEFAULT_RNA_PATH),
        )

    if dna_table is None:
        dna_table = build_empty_database_table("Charged monoisotopic mass")
    if rna_table is None:
        rna_table = build_empty_database_table("[M+H]+")

    match_cells_by_sheet = {
        sheet_name: build_match_column(dataset, dna_table, rna_table, mode)
        for sheet_name, dataset in dataset_sheets.items()
    }
    return export_workbook_results(
        datasets=dataset_sheets,
        match_cells_by_sheet=match_cells_by_sheet,
        source_path=state.dataset_path,
        output_dir=state.output_dir,
        formula_column_name=OUTPUT_FORMULA_COLUMN_NAME,
        name_column_name=OUTPUT_NAME_COLUMN_NAME,
    )


def build_empty_database_table(mass_column: str):
    from pandas import DataFrame

    return DataFrame(columns=["Short name", "Formula", mass_column])


class MatcherApp:
    def __init__(self, root: tk.Tk, state: AppState) -> None:
        self.root = root
        self.state = state
        self.root.title("MS Feature DB Matcher")
        self.root.configure(bg=COLORS["app_bg"])
        self.root.geometry("1040x660")
        self.root.minsize(920, 620)

        self.dataset_var = tk.StringVar(value="")
        self.dna_var = tk.StringVar(value=str(state.dna_db_path))
        self.rna_var = tk.StringVar(value=str(state.rna_db_path))
        self.mode_var = tk.StringVar(value=MatchMode.BOTH.value)
        self.status_var = tk.StringVar(value=f"Output folder: {state.output_dir}")
        self.status_title_var = tk.StringVar()
        self.header_badge_var = tk.StringVar()
        self.summary_var = tk.StringVar()
        self.dataset_badge_var = tk.StringVar()
        self.dna_badge_var = tk.StringVar()
        self.rna_badge_var = tk.StringVar()

        self.mode_tiles: dict[MatchMode, dict[str, tk.Widget]] = {}
        self.run_button: tk.Button | None = None
        self.header_badge_label: tk.Label | None = None
        self.status_frame: tk.Frame | None = None
        self.status_title_label: tk.Label | None = None
        self.status_detail_label: tk.Label | None = None

        for var in (self.dataset_var, self.dna_var, self.rna_var, self.mode_var):
            var.trace_add("write", self._on_ui_state_change)

        self._build()
        self._refresh_ui()

    def _build(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        shell = tk.Frame(self.root, bg=COLORS["app_bg"], padx=24, pady=24)
        shell.grid(sticky="nsew")
        shell.columnconfigure(0, weight=1)
        shell.rowconfigure(1, weight=1)

        header = tk.Frame(shell, bg=COLORS["app_bg"])
        header.grid(row=0, column=0, sticky="ew", pady=(0, 18))
        header.columnconfigure(0, weight=1)

        header_text = tk.Frame(header, bg=COLORS["app_bg"])
        header_text.grid(row=0, column=0, sticky="w")
        tk.Label(
            header_text,
            text="MS Feature DB Matcher",
            bg=COLORS["app_bg"],
            fg=COLORS["title"],
            font=FONTS["title"],
        ).grid(row=0, column=0, sticky="w")
        tk.Label(
            header_text,
            text="Match dataset features against DNA and RNA databases with a 20 ppm rule.",
            bg=COLORS["app_bg"],
            fg=COLORS["muted"],
            font=FONTS["subtitle"],
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        self.header_badge_label = tk.Label(
            header,
            textvariable=self.header_badge_var,
            bg=COLORS["warning_bg"],
            fg=COLORS["warning_fg"],
            font=FONTS["badge"],
            padx=12,
            pady=6,
        )
        self.header_badge_label.grid(row=0, column=1, sticky="e")

        body = tk.Frame(shell, bg=COLORS["app_bg"])
        body.grid(row=1, column=0, sticky="nsew")
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)

        left_card = self._create_card(body, "Input Files")
        left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        left_card.columnconfigure(0, weight=1)

        self._add_file_picker(
            left_card,
            row=0,
            label="Dataset",
            variable=self.dataset_var,
            badge_var=self.dataset_badge_var,
            command=self._choose_dataset,
            filetypes=[
                ("Supported files", "*.csv *.tsv *.xlsx *.xls"),
                ("All files", "*.*"),
            ],
        )
        self._add_file_picker(
            left_card,
            row=1,
            label="DNA Database",
            variable=self.dna_var,
            badge_var=self.dna_badge_var,
            command=self._choose_dna_db,
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")],
        )
        self._add_file_picker(
            left_card,
            row=2,
            label="RNA Database",
            variable=self.rna_var,
            badge_var=self.rna_badge_var,
            command=self._choose_rna_db,
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")],
        )

        right_column = tk.Frame(body, bg=COLORS["app_bg"])
        right_column.grid(row=0, column=1, sticky="nsew")
        right_column.rowconfigure(1, weight=1)

        mode_card = self._create_card(right_column, "Matching Mode")
        mode_card.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        for column in range(3):
            mode_card.columnconfigure(column, weight=1)

        for index, mode in enumerate((MatchMode.DNA, MatchMode.RNA, MatchMode.BOTH)):
            tile = self._create_mode_tile(mode_card, mode)
            tile["frame"].grid(row=1, column=index, sticky="nsew", padx=(0 if index == 0 else 8, 0))

        summary_card = self._create_card(right_column, "Run Summary")
        summary_card.grid(row=1, column=0, sticky="nsew")
        summary_card.columnconfigure(0, weight=1)
        self.summary_label = tk.Label(
            summary_card,
            textvariable=self.summary_var,
            bg=COLORS["card_bg"],
            fg=COLORS["text"],
            justify="left",
            anchor="nw",
            wraplength=300,
            font=FONTS["text"],
        )
        self.summary_label.grid(row=1, column=0, sticky="nsew")

        footer = tk.Frame(shell, bg=COLORS["app_bg"])
        footer.grid(row=2, column=0, sticky="ew", pady=(18, 0))
        footer.columnconfigure(0, weight=1)

        self.status_frame = tk.Frame(
            footer,
            bg=COLORS["ready_bg"],
            highlightthickness=1,
            highlightbackground=COLORS["card_border"],
            padx=16,
            pady=14,
        )
        self.status_frame.grid(row=0, column=0, sticky="ew", padx=(0, 12))
        self.status_frame.columnconfigure(0, weight=1)
        self.status_title_label = tk.Label(
            self.status_frame,
            textvariable=self.status_title_var,
            bg=COLORS["ready_bg"],
            fg=COLORS["ready_fg"],
            font=FONTS["label"],
            anchor="w",
        )
        self.status_title_label.grid(row=0, column=0, sticky="w")
        self.status_detail_label = tk.Label(
            self.status_frame,
            textvariable=self.status_var,
            bg=COLORS["ready_bg"],
            fg=COLORS["text"],
            font=FONTS["small"],
            anchor="w",
            justify="left",
            wraplength=560,
        )
        self.status_detail_label.grid(row=1, column=0, sticky="w", pady=(4, 0))

        button_bar = tk.Frame(footer, bg=COLORS["app_bg"])
        button_bar.grid(row=0, column=1, sticky="e")

        open_button = self._make_button(
            button_bar,
            text="Open Output Folder",
            command=self._open_output,
            primary=False,
            width=18,
        )
        open_button.grid(row=0, column=0, padx=(0, 10))

        self.run_button = self._make_button(
            button_bar,
            text="Run Matching",
            command=self._run,
            primary=True,
            width=16,
        )
        self.run_button.grid(row=0, column=1)

    def _create_card(self, parent: tk.Widget, title: str) -> tk.Frame:
        outer = tk.Frame(
            parent,
            bg=COLORS["card_bg"],
            highlightthickness=1,
            highlightbackground=COLORS["card_border"],
            padx=18,
            pady=18,
        )
        tk.Label(
            outer,
            text=title,
            bg=COLORS["card_bg"],
            fg=COLORS["title"],
            font=FONTS["card_title"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w", pady=(0, 14))
        return outer

    def _add_file_picker(
        self,
        frame: tk.Frame,
        row: int,
        label: str,
        variable: tk.StringVar,
        badge_var: tk.StringVar,
        command,
        filetypes,
    ) -> None:
        row_frame = tk.Frame(frame, bg=COLORS["card_bg"])
        row_frame.grid(row=row + 1, column=0, sticky="ew", pady=(0, 14 if row < 2 else 0))
        row_frame.columnconfigure(0, weight=1)

        header = tk.Frame(row_frame, bg=COLORS["card_bg"])
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        header.columnconfigure(0, weight=1)

        tk.Label(
            header,
            text=label,
            bg=COLORS["card_bg"],
            fg=COLORS["title"],
            font=FONTS["label"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        badge = tk.Label(
            header,
            textvariable=badge_var,
            bg=COLORS["soft_bg"],
            fg=COLORS["muted"],
            font=FONTS["badge"],
            padx=10,
            pady=3,
        )
        badge.grid(row=0, column=1, sticky="e")

        entry = tk.Entry(
            row_frame,
            textvariable=variable,
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=COLORS["card_border"],
            highlightcolor=COLORS["primary"],
            bg=COLORS["input_bg"],
            fg=COLORS["text"],
            font=FONTS["text"],
            insertbackground=COLORS["title"],
        )
        entry.grid(row=1, column=0, sticky="ew", ipadx=10, ipady=10, padx=(0, 10))

        browse = self._make_button(row_frame, text="Browse", command=command, primary=False, width=10)
        browse.grid(row=1, column=1, sticky="e")
        browse.configure(command=lambda: command(filetypes))

    def _create_mode_tile(self, parent: tk.Frame, mode: MatchMode) -> dict[str, tk.Widget]:
        frame = tk.Frame(
            parent,
            bg=COLORS["secondary_bg"],
            highlightthickness=1,
            highlightbackground=COLORS["secondary_border"],
            cursor="hand2",
            padx=12,
            pady=12,
        )
        title = tk.Label(
            frame,
            text=MODE_META[mode]["title"],
            bg=COLORS["secondary_bg"],
            fg=COLORS["title"],
            font=FONTS["label"],
            cursor="hand2",
        )
        title.grid(row=0, column=0, sticky="w")
        subtitle = tk.Label(
            frame,
            text=MODE_META[mode]["subtitle"],
            bg=COLORS["secondary_bg"],
            fg=COLORS["muted"],
            font=FONTS["small"],
            justify="left",
            wraplength=150,
            cursor="hand2",
        )
        subtitle.grid(row=1, column=0, sticky="w", pady=(6, 0))

        for widget in (frame, title, subtitle):
            widget.bind("<Button-1>", lambda _event, selected=mode: self._select_mode(selected))

        self.mode_tiles[mode] = {"frame": frame, "title": title, "subtitle": subtitle}
        return self.mode_tiles[mode]

    def _make_button(
        self,
        parent: tk.Widget,
        text: str,
        command,
        primary: bool,
        width: int,
    ) -> tk.Button:
        bg = COLORS["primary"] if primary else COLORS["secondary_bg"]
        fg = COLORS["button_text"] if primary else COLORS["title"]
        active_bg = COLORS["primary_active"] if primary else COLORS["secondary_hover"]
        border = COLORS["primary"] if primary else COLORS["secondary_border"]
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            activebackground=active_bg,
            activeforeground=fg,
            highlightthickness=1,
            highlightbackground=border,
            bd=0,
            relief="flat",
            font=FONTS["button"],
            padx=18,
            pady=12,
            cursor="hand2",
            width=width,
        )

    def _choose_dataset(self, filetypes) -> None:
        path = filedialog.askopenfilename(title="Select dataset", filetypes=filetypes)
        if path:
            self.state.dataset_path = Path(path)
            self.dataset_var.set(path)

    def _choose_dna_db(self, filetypes) -> None:
        path = filedialog.askopenfilename(title="Select DNA database", filetypes=filetypes)
        if path:
            self.state.dna_db_path = Path(path)
            self.dna_var.set(path)

    def _choose_rna_db(self, filetypes) -> None:
        path = filedialog.askopenfilename(title="Select RNA database", filetypes=filetypes)
        if path:
            self.state.rna_db_path = Path(path)
            self.rna_var.set(path)

    def _select_mode(self, mode: MatchMode) -> None:
        self.mode_var.set(mode.value)

    def _on_ui_state_change(self, *_args) -> None:
        self._refresh_ui()

    def _refresh_ui(self) -> None:
        dataset_text = self.dataset_var.get().strip()
        dna_path = Path(self.dna_var.get()) if self.dna_var.get().strip() else DEFAULT_DNA_PATH
        rna_path = Path(self.rna_var.get()) if self.rna_var.get().strip() else DEFAULT_RNA_PATH
        mode = MatchMode(self.mode_var.get())

        self.dataset_badge_var.set("Required" if not dataset_text else "Ready")
        self.dna_badge_var.set(path_badge_text(dna_path, DEFAULT_DNA_PATH))
        self.rna_badge_var.set(path_badge_text(rna_path, DEFAULT_RNA_PATH))
        self.header_badge_var.set("Dataset Missing" if not dataset_text else "Dataset Selected")

        if self.header_badge_label is not None:
            if dataset_text:
                self.header_badge_label.configure(bg=COLORS["ready_bg"], fg=COLORS["ready_fg"])
            else:
                self.header_badge_label.configure(bg=COLORS["warning_bg"], fg=COLORS["warning_fg"])

        self.summary_var.set(
            "\n".join(
                [
                    describe_mode(mode),
                    "Excel inputs: every worksheet with a supported mass column is matched and exported.",
                    "Accepted mass columns: Feature, Mz, m/z, Mz/RT, Precursor Ion m/z, Charged monoisotopic mass, [M+H]+ Protonated Mass.",
                    "Parsing rule: if a value contains '/', only the text before '/' is used as m/z.",
                    "Tolerance: abs(feature_mz - db_mz) / db_mz * 1e6 <= 20.",
                    f"Output: Matched Formula + Matched Short name appended to {self.state.output_dir}.",
                    "Formatting: DNA names stay blue and RNA names stay red.",
                ]
            )
        )

        self._refresh_mode_tiles(mode)
        self._refresh_status()

        if self.run_button is not None:
            self.run_button.configure(state="normal" if dataset_text else "disabled")

    def _refresh_mode_tiles(self, selected_mode: MatchMode) -> None:
        for mode, widgets in self.mode_tiles.items():
            selected = mode == selected_mode
            frame_bg = COLORS["primary"] if selected else COLORS["secondary_bg"]
            title_fg = COLORS["button_text"] if selected else COLORS["title"]
            subtitle_fg = "#D6F4EF" if selected else COLORS["muted"]
            border = COLORS["primary"] if selected else COLORS["secondary_border"]
            widgets["frame"].configure(bg=frame_bg, highlightbackground=border)
            widgets["title"].configure(bg=frame_bg, fg=title_fg)
            widgets["subtitle"].configure(bg=frame_bg, fg=subtitle_fg)

    def _refresh_status(self) -> None:
        appearance = status_appearance(self.status_var.get())
        self.status_title_var.set(appearance["title"])
        if self.status_frame is not None:
            self.status_frame.configure(bg=appearance["background"])
        if self.status_title_label is not None:
            self.status_title_label.configure(bg=appearance["background"], fg=appearance["foreground"])
        if self.status_detail_label is not None:
            self.status_detail_label.configure(bg=appearance["background"], fg=COLORS["text"])

    def _run(self) -> None:
        self.state.dna_db_path = Path(self.dna_var.get())
        self.state.rna_db_path = Path(self.rna_var.get())
        dataset_text = self.dataset_var.get().strip()
        self.state.dataset_path = Path(dataset_text) if dataset_text else None

        try:
            result_path = run_matching(self.state, MatchMode(self.mode_var.get()))
        except Exception as exc:
            messagebox.showerror("Matching Failed", str(exc))
            self.status_var.set(f"Failed: {exc}")
            self._refresh_status()
            return

        messagebox.showinfo("Matching Complete", f"Output saved to:\n{result_path}")
        self.status_var.set(f"Saved result to: {result_path}")
        self._refresh_status()

    def _open_output(self) -> None:
        try:
            open_output_folder(self.state.output_dir)
            self.status_var.set(f"Output folder: {self.state.output_dir}")
            self._refresh_status()
        except Exception as exc:
            messagebox.showerror("Open Output Folder Failed", str(exc))
            self.status_var.set(f"Failed: {exc}")
            self._refresh_status()


def launch_app() -> None:
    root = tk.Tk()
    MatcherApp(root, AppState.create())
    root.mainloop()
