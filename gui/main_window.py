"""
CPU Freeesh — main GUI window.
Dark gaming theme built entirely with tkinter + ttk (no extra UI deps).
"""

import threading
import time
import logging
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

import psutil

from core import backup_restore, memory_optimizer, power_manager, process_manager, service_manager
from core.logger_setup import setup as setup_logging
from core.backup_restore import SystemSnapshot

# ── Colour palette ─────────────────────────────────────────────────────────────
BG        = "#0a0a0f"
SURFACE   = "#12121e"
CARD      = "#1a1a2c"
BORDER    = "#2a2a42"
GREEN     = "#00e87d"
CYAN      = "#00c8f0"
RED       = "#ff4757"
ORANGE    = "#ff6b35"
TEXT      = "#eeeef4"
TEXT_DIM  = "#7777a0"
TEXT_MUT  = "#3a3a55"
# ───────────────────────────────────────────────────────────────────────────────

VERSION = "1.0.0"

logger = logging.getLogger(__name__)


class MainWindow:
    def __init__(self) -> None:
        setup_logging()

        self.root = tk.Tk()
        self.game_mode_active = tk.BooleanVar(value=False)

        self._monitor_running = True
        self._game_pid: int | None = None

        self._setup_window()
        self._apply_ttk_styles()
        self._build_ui()
        self._start_monitor()

        # Restore indicator if a previous backup exists
        if backup_restore.has_backup():
            self._log("⚠  Previous Game Mode session detected — click Restore if needed.", ORANGE)

    # ── Window setup ───────────────────────────────────────────────────────────

    def _setup_window(self) -> None:
        self.root.title(f"CPU Freeesh  v{VERSION}")
        self.root.geometry("860x680")
        self.root.minsize(720, 580)
        self.root.configure(bg=BG)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        try:
            self.root.iconbitmap(default="assets/icon.ico")
        except Exception:
            pass

    def _apply_ttk_styles(self) -> None:
        style = ttk.Style(self.root)
        style.theme_use("clam")

        style.configure(".", background=BG, foreground=TEXT, fieldbackground=CARD,
                        bordercolor=BORDER, troughcolor=CARD, selectbackground=CARD,
                        selectforeground=GREEN, font=("Segoe UI", 10))

        style.configure("TFrame", background=BG)
        style.configure("Card.TFrame", background=CARD, relief="flat")

        style.configure("TLabel", background=BG, foreground=TEXT)
        style.configure("Dim.TLabel", background=BG, foreground=TEXT_DIM)
        style.configure("Card.TLabel", background=CARD, foreground=TEXT)
        style.configure("CardDim.TLabel", background=CARD, foreground=TEXT_DIM)

        # Big action buttons
        style.configure("Green.TButton",
                        background=GREEN, foreground="#000000",
                        font=("Segoe UI", 11, "bold"), padding=(18, 8),
                        relief="flat", borderwidth=0)
        style.map("Green.TButton",
                  background=[("active", "#00c86a"), ("disabled", TEXT_MUT)],
                  foreground=[("disabled", "#444444")])

        style.configure("Red.TButton",
                        background=RED, foreground="#ffffff",
                        font=("Segoe UI", 11, "bold"), padding=(18, 8),
                        relief="flat", borderwidth=0)
        style.map("Red.TButton",
                  background=[("active", "#e03040"), ("disabled", TEXT_MUT)])

        style.configure("Ghost.TButton",
                        background=CARD, foreground=TEXT_DIM,
                        font=("Segoe UI", 9), padding=(8, 4),
                        relief="flat", borderwidth=1)
        style.map("Ghost.TButton",
                  background=[("active", BORDER)],
                  foreground=[("active", TEXT)])

        # Treeview
        style.configure("Treeview",
                        background=CARD, foreground=TEXT,
                        fieldbackground=CARD, rowheight=24,
                        borderwidth=0, font=("Segoe UI", 9))
        style.configure("Treeview.Heading",
                        background=SURFACE, foreground=TEXT_DIM,
                        font=("Segoe UI", 9, "bold"), relief="flat")
        style.map("Treeview",
                  background=[("selected", BORDER)],
                  foreground=[("selected", GREEN)])

        style.configure("TSeparator", background=BORDER)
        style.configure("TScrollbar", background=CARD, troughcolor=SURFACE,
                        arrowcolor=TEXT_DIM, borderwidth=0)

    # ── UI construction ────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        self._build_header()
        ttk.Separator(self.root, orient="horizontal").pack(fill="x", padx=0)
        self._build_stats_bar()
        ttk.Separator(self.root, orient="horizontal").pack(fill="x", padx=0)
        self._build_action_row()
        ttk.Separator(self.root, orient="horizontal").pack(fill="x", padx=0)

        paned = tk.PanedWindow(self.root, orient="vertical",
                               bg=BG, sashwidth=4, sashrelief="flat",
                               handlesize=0)
        paned.pack(fill="both", expand=True, padx=0, pady=0)

        self._build_process_panel(paned)
        self._build_log_panel(paned)

        self._build_status_bar()

    def _build_header(self) -> None:
        hdr = tk.Frame(self.root, bg=SURFACE, height=52)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        tk.Label(hdr, text="⚡ CPU Freeesh", bg=SURFACE, fg=GREEN,
                 font=("Segoe UI", 16, "bold")).pack(side="left", padx=18, pady=10)

        tk.Label(hdr, text=f"v{VERSION}", bg=SURFACE, fg=TEXT_DIM,
                 font=("Segoe UI", 9)).pack(side="left", pady=10)

        tk.Label(hdr, text="Game Performance Optimizer", bg=SURFACE, fg=TEXT_DIM,
                 font=("Segoe UI", 9, "italic")).pack(side="right", padx=18, pady=10)

    def _build_stats_bar(self) -> None:
        bar = tk.Frame(self.root, bg=SURFACE, height=44)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        def stat_block(parent, label_text: str, var: tk.StringVar, color: str):
            blk = tk.Frame(parent, bg=SURFACE)
            blk.pack(side="left", padx=16, pady=6)
            tk.Label(blk, text=label_text, bg=SURFACE, fg=TEXT_DIM,
                     font=("Segoe UI", 8)).pack(side="left")
            tk.Label(blk, textvariable=var, bg=SURFACE, fg=color,
                     font=("Segoe UI", 11, "bold")).pack(side="left", padx=(4, 0))

        self._cpu_var  = tk.StringVar(value="—")
        self._ram_var  = tk.StringVar(value="—")
        self._plan_var = tk.StringVar(value="—")
        self._mode_var = tk.StringVar(value="OFF")

        stat_block(bar, "CPU", self._cpu_var, CYAN)
        stat_block(bar, "RAM", self._ram_var, CYAN)
        stat_block(bar, "Power Plan:", self._plan_var, TEXT_DIM)

        # Game mode indicator
        sep = tk.Frame(bar, bg=BORDER, width=1)
        sep.pack(side="left", fill="y", padx=12, pady=8)

        tk.Label(bar, text="GAME MODE", bg=SURFACE, fg=TEXT_DIM,
                 font=("Segoe UI", 8)).pack(side="left")
        self._mode_lbl = tk.Label(bar, textvariable=self._mode_var,
                                  bg=SURFACE, fg=RED,
                                  font=("Segoe UI", 11, "bold"))
        self._mode_lbl.pack(side="left", padx=(4, 0))

    def _build_action_row(self) -> None:
        row = tk.Frame(self.root, bg=BG, height=68)
        row.pack(fill="x")
        row.pack_propagate(False)

        inner = tk.Frame(row, bg=BG)
        inner.pack(expand=True, fill="both", padx=16, pady=12)

        self._activate_btn = ttk.Button(
            inner, text="🎮  ACTIVATE GAME MODE",
            style="Green.TButton",
            command=self._on_activate
        )
        self._activate_btn.pack(side="left", padx=(0, 8))

        self._restore_btn = ttk.Button(
            inner, text="↩  RESTORE SETTINGS",
            style="Red.TButton",
            command=self._on_restore,
            state="disabled"
        )
        self._restore_btn.pack(side="left")

        ttk.Button(inner, text="⟳ Refresh Processes",
                   style="Ghost.TButton",
                   command=self._refresh_processes).pack(side="right")

    def _build_process_panel(self, parent: tk.PanedWindow) -> None:
        frame = tk.Frame(parent, bg=BG)
        parent.add(frame, minsize=160)

        # Header
        hdr = tk.Frame(frame, bg=BG)
        hdr.pack(fill="x", padx=12, pady=(8, 4))
        tk.Label(hdr, text="PROCESS MANAGER", bg=BG, fg=TEXT_DIM,
                 font=("Segoe UI", 8, "bold")).pack(side="left")
        tk.Label(hdr, text="— select a process then use the action buttons below",
                 bg=BG, fg=TEXT_MUT, font=("Segoe UI", 8)).pack(side="left", padx=4)

        # Treeview
        tv_frame = tk.Frame(frame, bg=CARD, highlightbackground=BORDER,
                            highlightthickness=1)
        tv_frame.pack(fill="both", expand=True, padx=12, pady=(0, 4))

        cols = ("name", "cpu", "ram", "pid", "priority")
        self._tree = ttk.Treeview(tv_frame, columns=cols, show="headings",
                                  selectmode="browse")
        self._tree.heading("name",     text="Process",   anchor="w")
        self._tree.heading("cpu",      text="CPU %",     anchor="center")
        self._tree.heading("ram",      text="RAM (MB)",  anchor="center")
        self._tree.heading("pid",      text="PID",       anchor="center")
        self._tree.heading("priority", text="Priority",  anchor="center")

        self._tree.column("name",     width=260, anchor="w",      stretch=True)
        self._tree.column("cpu",      width=70,  anchor="center", stretch=False)
        self._tree.column("ram",      width=90,  anchor="center", stretch=False)
        self._tree.column("pid",      width=70,  anchor="center", stretch=False)
        self._tree.column("priority", width=110, anchor="center", stretch=False)

        vsb = ttk.Scrollbar(tv_frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # Action row
        act = tk.Frame(frame, bg=BG)
        act.pack(fill="x", padx=12, pady=(0, 8))

        ttk.Button(act, text="Kill Process",  style="Ghost.TButton",
                   command=self._on_kill).pack(side="left", padx=(0, 6))
        ttk.Button(act, text="↑ High Priority", style="Ghost.TButton",
                   command=self._on_high_priority).pack(side="left", padx=(0, 6))
        ttk.Button(act, text="↓ Low Priority", style="Ghost.TButton",
                   command=self._on_low_priority).pack(side="left")

        tk.Label(act, text="Tip: set your game to High Priority for best results.",
                 bg=BG, fg=TEXT_MUT, font=("Segoe UI", 8)).pack(side="right")

        self._refresh_processes()

    def _build_log_panel(self, parent: tk.PanedWindow) -> None:
        frame = tk.Frame(parent, bg=BG)
        parent.add(frame, minsize=100)

        hdr = tk.Frame(frame, bg=BG)
        hdr.pack(fill="x", padx=12, pady=(6, 2))
        tk.Label(hdr, text="ACTION LOG", bg=BG, fg=TEXT_DIM,
                 font=("Segoe UI", 8, "bold")).pack(side="left")
        ttk.Button(hdr, text="Clear", style="Ghost.TButton",
                   command=self._clear_log).pack(side="right")

        self._log_box = scrolledtext.ScrolledText(
            frame, bg=SURFACE, fg=TEXT_DIM, insertbackground=TEXT,
            font=("Consolas", 9), relief="flat", borderwidth=0,
            state="disabled", wrap="word", height=6,
        )
        self._log_box.pack(fill="both", expand=True, padx=12, pady=(0, 6))

        # Tag colours
        self._log_box.tag_configure("green",  foreground=GREEN)
        self._log_box.tag_configure("red",    foreground=RED)
        self._log_box.tag_configure("orange", foreground=ORANGE)
        self._log_box.tag_configure("cyan",   foreground=CYAN)
        self._log_box.tag_configure("dim",    foreground=TEXT_DIM)

    def _build_status_bar(self) -> None:
        bar = tk.Frame(self.root, bg=SURFACE, height=22)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        self._status_var = tk.StringVar(value="Ready")
        tk.Label(bar, textvariable=self._status_var,
                 bg=SURFACE, fg=TEXT_DIM, font=("Segoe UI", 8),
                 anchor="w").pack(side="left", padx=10, pady=2)

        tk.Label(bar, text="github.com/OTI/CPU-Freeesh",
                 bg=SURFACE, fg=TEXT_MUT, font=("Segoe UI", 8)).pack(side="right", padx=10)

    # ── Logging helpers ────────────────────────────────────────────────────────

    def _log(self, message: str, color: str = GREEN) -> None:
        tag_map = {
            GREEN:  "green",
            RED:    "red",
            ORANGE: "orange",
            CYAN:   "cyan",
        }
        tag = tag_map.get(color, "dim")

        def _insert():
            self._log_box.configure(state="normal")
            self._log_box.insert("end", f"  {message}\n", tag)
            self._log_box.see("end")
            self._log_box.configure(state="disabled")

        self.root.after(0, _insert)

    def _clear_log(self) -> None:
        self._log_box.configure(state="normal")
        self._log_box.delete("1.0", "end")
        self._log_box.configure(state="disabled")

    def _set_status(self, text: str) -> None:
        self.root.after(0, lambda: self._status_var.set(text))

    # ── Process table ──────────────────────────────────────────────────────────

    def _refresh_processes(self) -> None:
        def _work():
            procs = process_manager.get_processes()
            self.root.after(0, lambda: self._populate_tree(procs))
        threading.Thread(target=_work, daemon=True).start()

    def _populate_tree(self, procs: list) -> None:
        selected_pid = None
        sel = self._tree.selection()
        if sel:
            try:
                selected_pid = int(self._tree.item(sel[0])["values"][3])
            except (IndexError, ValueError):
                pass

        self._tree.delete(*self._tree.get_children())
        restore_iid = None
        for p in procs:
            iid = self._tree.insert(
                "", "end",
                values=(
                    p.name,
                    f"{p.cpu_percent:.1f}",
                    f"{p.memory_mb:.0f}",
                    p.pid,
                    process_manager.PRIORITY_LABELS.get(p.priority, str(p.priority)),
                ),
            )
            if p.pid == selected_pid:
                restore_iid = iid

        if restore_iid:
            self._tree.selection_set(restore_iid)

    def _selected_pid(self) -> int | None:
        sel = self._tree.selection()
        if not sel:
            return None
        try:
            return int(self._tree.item(sel[0])["values"][3])
        except (IndexError, ValueError):
            return None

    # ── Process actions ────────────────────────────────────────────────────────

    def _on_kill(self) -> None:
        pid = self._selected_pid()
        if pid is None:
            messagebox.showinfo("CPU Freeesh", "Select a process first.")
            return
        name = self._tree.item(self._tree.selection()[0])["values"][0]
        if not messagebox.askyesno("Kill Process",
                                   f"Terminate  {name}  (PID {pid})?\n\nUnsaved work will be lost."):
            return
        if process_manager.kill_process(pid):
            self._log(f"Killed: {name} (PID {pid})", RED)
        else:
            self._log(f"Could not kill {name} — access denied or protected process.", ORANGE)
        self._refresh_processes()

    def _on_high_priority(self) -> None:
        pid = self._selected_pid()
        if pid is None:
            messagebox.showinfo("CPU Freeesh", "Select a process first.")
            return
        name = self._tree.item(self._tree.selection()[0])["values"][0]
        if process_manager.set_process_priority(pid, process_manager.PRIORITY_HIGH):
            self._log(f"Set HIGH priority: {name} (PID {pid})", GREEN)
            self._game_pid = pid
        else:
            self._log(f"Could not change priority for {name}.", ORANGE)
        self._refresh_processes()

    def _on_low_priority(self) -> None:
        pid = self._selected_pid()
        if pid is None:
            messagebox.showinfo("CPU Freeesh", "Select a process first.")
            return
        name = self._tree.item(self._tree.selection()[0])["values"][0]
        if process_manager.set_process_priority(pid, process_manager.PRIORITY_BELOW_NORMAL):
            self._log(f"Lowered priority: {name} (PID {pid})", TEXT_DIM)
        else:
            self._log(f"Could not change priority for {name}.", ORANGE)
        self._refresh_processes()

    # ── Game Mode ─────────────────────────────────────────────────────────────

    def _on_activate(self) -> None:
        if self.game_mode_active.get():
            return
        self._activate_btn.configure(state="disabled")
        self._set_status("Activating Game Mode…")
        threading.Thread(target=self._activate_game_mode, daemon=True).start()

    def _activate_game_mode(self) -> None:
        self._log("── Activating Game Mode ──", CYAN)

        # 1. Save current power plan
        guid, name = power_manager.get_active_plan()
        self._log(f"Current power plan: {name}", TEXT_DIM)

        # 2. Switch to High Performance
        if power_manager.activate_high_performance():
            self._log("✓ Power plan → High Performance", GREEN)
        else:
            self._log("⚠  Could not switch power plan.", ORANGE)

        # 3. Stop background services
        self._log("Stopping background services…", TEXT_DIM)
        svc_backup = service_manager.optimize_services()
        stopped = [k for k, v in svc_backup.items() if v == "running"]
        if stopped:
            self._log(f"✓ Stopped services: {', '.join(stopped)}", GREEN)
        else:
            self._log("  No running optimizable services found.", TEXT_DIM)

        # 4. Lower background process priorities
        game_pids = {self._game_pid} if self._game_pid else set()
        count = process_manager.lower_background_priorities(excluded_pids=game_pids)
        self._log(f"✓ Lowered priority on {count} background processes", GREEN)

        # 5. Free RAM
        trimmed, freed_mb = memory_optimizer.free_background_ram(game_pids=game_pids)
        self._log(f"✓ RAM trim: {trimmed} processes, ~{freed_mb:.0f} MB freed", GREEN)

        # 6. Save backup
        snap = SystemSnapshot(
            power_plan_guid=guid,
            power_plan_name=name,
            services=svc_backup,
            priorities_lowered=True,
        )
        backup_restore.save(snap)

        self._log("── Game Mode ACTIVE ──", GREEN)
        self.root.after(0, self._set_game_mode_ui, True)
        self._set_status("Game Mode is ACTIVE")

    def _on_restore(self) -> None:
        if not self.game_mode_active.get():
            return
        self._restore_btn.configure(state="disabled")
        self._set_status("Restoring settings…")
        threading.Thread(target=self._restore_settings, daemon=True).start()

    def _restore_settings(self) -> None:
        self._log("── Restoring System Settings ──", ORANGE)
        snap = backup_restore.load()

        if snap:
            # Power plan
            if power_manager.restore_plan(snap.power_plan_guid):
                self._log(f"✓ Power plan → {snap.power_plan_name}", GREEN)
            else:
                self._log("⚠  Could not restore power plan.", ORANGE)

            # Services
            service_manager.restore_services(snap.services)
            restored = [k for k, v in snap.services.items() if v == "running"]
            if restored:
                self._log(f"✓ Restarted services: {', '.join(restored)}", GREEN)

            # Priorities
            if snap.priorities_lowered:
                count = process_manager.restore_normal_priorities()
                self._log(f"✓ Restored Normal priority on {count} processes", GREEN)

            backup_restore.clear()
        else:
            self._log("No backup found — nothing to restore.", ORANGE)

        self._log("── Settings Restored ──", CYAN)
        self.root.after(0, self._set_game_mode_ui, False)
        self._set_status("Ready")
        self._refresh_processes()

    def _set_game_mode_ui(self, active: bool) -> None:
        self.game_mode_active.set(active)
        if active:
            self._mode_var.set("ON")
            self._mode_lbl.configure(fg=GREEN)
            self._activate_btn.configure(state="disabled")
            self._restore_btn.configure(state="normal")
        else:
            self._mode_var.set("OFF")
            self._mode_lbl.configure(fg=RED)
            self._activate_btn.configure(state="normal")
            self._restore_btn.configure(state="disabled")

    # ── Real-time monitor ─────────────────────────────────────────────────────

    def _start_monitor(self) -> None:
        threading.Thread(target=self._monitor_loop, daemon=True).start()

    def _monitor_loop(self) -> None:
        psutil.cpu_percent(interval=None)  # prime
        while self._monitor_running:
            try:
                cpu = psutil.cpu_percent(interval=1)
                ram = psutil.virtual_memory().percent
                _, plan_name = power_manager.get_active_plan()

                self.root.after(0, self._update_stats, cpu, ram, plan_name)
            except Exception:
                pass
            time.sleep(2)

    def _update_stats(self, cpu: float, ram: float, plan: str) -> None:
        self._cpu_var.set(f"{cpu:.0f}%")
        self._ram_var.set(f"{ram:.0f}%")
        self._plan_var.set(plan)

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def _on_close(self) -> None:
        if self.game_mode_active.get():
            if not messagebox.askyesno(
                "CPU Freeesh",
                "Game Mode is still active.\n\n"
                "Close without restoring settings?\n"
                "(You can restore later by reopening CPU Freeesh.)",
            ):
                return
        self._monitor_running = False
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()
