"""
CDR (Call Detail Record) Analyzer - GUI Application
Author: Generated for Academic Project
Requirements: pip install pandas matplotlib numpy
Run: python cdr_analyzer.py
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import numpy as np
import random
from datetime import datetime, timedelta

# ─────────────────────────────────────────────
#  DUMMY DATA GENERATOR
# ─────────────────────────────────────────────
def generate_dummy_cdr(n=200):
    contacts = {
        "Rahul Sharma":    "9876543210",
        "Priya Patel":     "9845012345",
        "Amit Verma":      "9123456789",
        "Sunita Rao":      "9001234567",
        "Vikram Singh":    "9812345670",
        "Neha Gupta":      "9734512345",
        "Rohan Mehta":     "9654321098",
        "Kavya Nair":      "9543210987",
        "Deepak Joshi":    "9432109876",
        "Anjali Kumar":    "9321098765",
    }
    names   = list(contacts.keys())
    numbers = list(contacts.values())

    call_types = ["Incoming", "Outgoing", "Missed"]
    weights    = [0.40, 0.45, 0.15]

    start = datetime(2024, 1, 1)
    records = []
    for _ in range(n):
        idx    = random.randint(0, len(names) - 1)
        ctype  = random.choices(call_types, weights)[0]
        dt     = start + timedelta(
            days=random.randint(0, 179),
            hours=random.randint(7, 22),
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59),
        )
        dur = 0 if ctype == "Missed" else random.randint(10, 1800)
        records.append({
            "Date":        dt.strftime("%Y-%m-%d"),
            "Time":        dt.strftime("%H:%M:%S"),
            "DateTime":    dt,
            "Name":        names[idx],
            "Number":      numbers[idx],
            "Call Type":   ctype,
            "Duration(s)": dur,
            "Duration(m)": round(dur / 60, 2),
        })
    df = pd.DataFrame(records).sort_values("DateTime").reset_index(drop=True)
    df["Week"] = pd.to_datetime(df["Date"]).dt.isocalendar().week.astype(str)
    df["Month"] = pd.to_datetime(df["Date"]).dt.strftime("%b")
    return df


# ─────────────────────────────────────────────
#  COLOUR PALETTE
# ─────────────────────────────────────────────
BG       = "#0f1117"
CARD     = "#1a1d27"
ACCENT   = "#4f8ef7"
GREEN    = "#43e97b"
ORANGE   = "#f7971e"
RED      = "#f64f59"
TEXT     = "#e8eaf0"
SUBTEXT  = "#8b8fa8"
CHART_BG = "#12151e"

PALETTE  = [ACCENT, GREEN, ORANGE, RED, "#a78bfa", "#38bdf8", "#fb7185", "#34d399"]


# ─────────────────────────────────────────────
#  MAIN APPLICATION
# ─────────────────────────────────────────────
class CDRAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("📞 CDR Analyzer — Call Detail Record Dashboard")
        self.root.geometry("1280x820")
        self.root.configure(bg=BG)
        self.root.resizable(True, True)

        self.df = generate_dummy_cdr(200)
        self.filtered_df = self.df.copy()

        self._build_ui()
        self._update_stats()
        self._draw_all_charts()

    # ── TOP HEADER ──────────────────────────
    def _build_ui(self):
        # Header
        header = tk.Frame(self.root, bg="#0d1525", height=64)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="📞  CDR Analyzer", font=("Courier New", 20, "bold"),
                 bg="#0d1525", fg=ACCENT).pack(side="left", padx=24, pady=14)
        tk.Label(header, text="Call Detail Record Dashboard",
                 font=("Courier New", 11), bg="#0d1525", fg=SUBTEXT).pack(side="left", pady=14)

        # Buttons on right
        btn_frame = tk.Frame(header, bg="#0d1525")
        btn_frame.pack(side="right", padx=16)
        tk.Button(btn_frame, text="⟳  Refresh Data", command=self._refresh,
                  bg=ACCENT, fg="white", font=("Courier New", 10, "bold"),
                  relief="flat", padx=12, pady=6, cursor="hand2").pack(side="left", padx=4)
        tk.Button(btn_frame, text="📂  Load CSV", command=self._load_csv,
                  bg=CARD, fg=TEXT, font=("Courier New", 10),
                  relief="flat", padx=12, pady=6, cursor="hand2").pack(side="left", padx=4)
        tk.Button(btn_frame, text="💾  Export CSV", command=self._export_csv,
                  bg=CARD, fg=TEXT, font=("Courier New", 10),
                  relief="flat", padx=12, pady=6, cursor="hand2").pack(side="left", padx=4)

        # Filter bar
        filter_bar = tk.Frame(self.root, bg="#131620", pady=8)
        filter_bar.pack(fill="x")

        tk.Label(filter_bar, text="Filter:", bg="#131620", fg=SUBTEXT,
                 font=("Courier New", 10)).pack(side="left", padx=(16, 4))

        self.filter_type = ttk.Combobox(filter_bar, values=["All", "Incoming", "Outgoing", "Missed"],
                                        width=12, state="readonly")
        self.filter_type.set("All")
        self.filter_type.pack(side="left", padx=4)
        self.filter_type.bind("<<ComboboxSelected>>", lambda e: self._apply_filter())

        tk.Label(filter_bar, text="Contact:", bg="#131620", fg=SUBTEXT,
                 font=("Courier New", 10)).pack(side="left", padx=(12, 4))
        names = ["All"] + sorted(self.df["Name"].unique().tolist())
        self.filter_contact = ttk.Combobox(filter_bar, values=names, width=16, state="readonly")
        self.filter_contact.set("All")
        self.filter_contact.pack(side="left", padx=4)
        self.filter_contact.bind("<<ComboboxSelected>>", lambda e: self._apply_filter())

        # Stat cards row
        self.stat_frame = tk.Frame(self.root, bg=BG, pady=12)
        self.stat_frame.pack(fill="x", padx=16)
        self.stat_labels = {}
        stats = [
            ("total",    "Total Calls",     "📞", ACCENT),
            ("incoming", "Incoming",         "📥", GREEN),
            ("outgoing", "Outgoing",         "📤", ORANGE),
            ("missed",   "Missed",           "❌", RED),
            ("duration", "Avg Duration",     "⏱️", "#a78bfa"),
            ("contacts", "Unique Contacts",  "👥", "#38bdf8"),
        ]
        for key, label, icon, color in stats:
            card = tk.Frame(self.stat_frame, bg=CARD, padx=18, pady=10,
                            relief="flat", bd=0)
            card.pack(side="left", expand=True, fill="both", padx=6)
            tk.Label(card, text=icon + "  " + label, bg=CARD, fg=SUBTEXT,
                     font=("Courier New", 9)).pack(anchor="w")
            lbl = tk.Label(card, text="—", bg=CARD, fg=color,
                           font=("Courier New", 18, "bold"))
            lbl.pack(anchor="w")
            self.stat_labels[key] = lbl

        # Notebook (tabs)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=CARD, foreground=TEXT,
                        font=("Courier New", 10, "bold"), padding=[16, 8])
        style.map("TNotebook.Tab", background=[("selected", ACCENT)],
                  foreground=[("selected", "white")])

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        self.tab_charts  = tk.Frame(self.notebook, bg=BG)
        self.tab_table   = tk.Frame(self.notebook, bg=BG)
        self.tab_summary = tk.Frame(self.notebook, bg=BG)

        self.notebook.add(self.tab_charts,  text="📊  Charts")
        self.notebook.add(self.tab_table,   text="📋  Call Records")
        self.notebook.add(self.tab_summary, text="📈  Summary")

        self._build_charts_tab()
        self._build_table_tab()
        self._build_summary_tab()

    # ── CHARTS TAB ──────────────────────────
    def _build_charts_tab(self):
        self.fig = Figure(figsize=(14, 7), facecolor=CHART_BG, tight_layout=True)
        self.fig.patch.set_facecolor(CHART_BG)

        canvas = FigureCanvasTkAgg(self.fig, master=self.tab_charts)
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)
        toolbar_frame = tk.Frame(self.tab_charts, bg=BG)
        toolbar_frame.pack(fill="x")
        NavigationToolbar2Tk(canvas, toolbar_frame)
        self.chart_canvas = canvas

    def _draw_all_charts(self):
        df = self.filtered_df
        self.fig.clear()

        gs = gridspec.GridSpec(2, 2, figure=self.fig,
                               hspace=0.45, wspace=0.35)
        axes = [self.fig.add_subplot(gs[r, c]) for r in range(2) for c in range(2)]
        for ax in axes:
            ax.set_facecolor(CARD)
            for spine in ax.spines.values():
                spine.set_edgecolor("#2a2d3e")
            ax.tick_params(colors=SUBTEXT, labelsize=8)
            ax.title.set_color(TEXT)
            ax.xaxis.label.set_color(SUBTEXT)
            ax.yaxis.label.set_color(SUBTEXT)

        # 1) Calls per day
        ax1 = axes[0]
        daily = df.groupby("Date").size().reset_index(name="Count")
        daily["Date"] = pd.to_datetime(daily["Date"])
        daily = daily.sort_values("Date").tail(30)
        ax1.bar(range(len(daily)), daily["Count"], color=ACCENT, alpha=0.85, width=0.7)
        ax1.set_title("📅  Calls Per Day (Last 30 Days)", fontsize=10, pad=10)
        ax1.set_xlabel("Day")
        ax1.set_ylabel("No. of Calls")
        ax1.set_xticks(range(0, len(daily), max(1, len(daily)//6)))
        ax1.set_xticklabels(
            [d.strftime("%d %b") for d in daily["Date"].iloc[::max(1, len(daily)//6)]],
            rotation=30, ha="right", fontsize=7)

        # 2) Pie – Incoming vs Outgoing vs Missed
        ax2 = axes[1]
        counts = df["Call Type"].value_counts()
        wedge_props = dict(width=0.55, edgecolor=CHART_BG, linewidth=2)
        ax2.pie(counts.values, labels=counts.index, autopct="%1.1f%%",
                colors=[GREEN, ORANGE, RED][:len(counts)],
                wedgeprops=wedge_props, textprops={"color": TEXT, "fontsize": 9},
                pctdistance=0.75, startangle=140)
        ax2.set_title("📞  Call Type Distribution", fontsize=10, pad=10)

        # 3) Top contacts bar
        ax3 = axes[2]
        top = df[df["Call Type"] != "Missed"].groupby("Name")["Duration(m)"].sum().nlargest(6)
        bars = ax3.barh(top.index, top.values,
                        color=PALETTE[:len(top)], alpha=0.88, height=0.6)
        ax3.set_title("🏆  Top Contacts by Talk Time (min)", fontsize=10, pad=10)
        ax3.set_xlabel("Total Duration (min)")
        for bar, val in zip(bars, top.values):
            ax3.text(val + 0.3, bar.get_y() + bar.get_height() / 2,
                     f"{val:.1f}m", va="center", color=TEXT, fontsize=7)

        # 4) Avg duration per contact
        ax4 = axes[3]
        avg_dur = df[df["Call Type"] != "Missed"].groupby("Call Type")["Duration(m)"].mean()
        monthly = df[df["Call Type"] != "Missed"].groupby("Month")["Duration(m)"].mean()
        months_order = ["Jan","Feb","Mar","Apr","May","Jun",
                        "Jul","Aug","Sep","Oct","Nov","Dec"]
        monthly = monthly.reindex([m for m in months_order if m in monthly.index])
        ax4.plot(monthly.index, monthly.values, color=GREEN,
                 linewidth=2.5, marker="o", markersize=5)
        ax4.fill_between(range(len(monthly)), monthly.values,
                         alpha=0.15, color=GREEN)
        ax4.set_xticks(range(len(monthly)))
        ax4.set_xticklabels(monthly.index, rotation=30, ha="right", fontsize=8)
        ax4.set_title("📈  Avg Call Duration by Month (min)", fontsize=10, pad=10)
        ax4.set_ylabel("Avg Duration (min)")

        self.chart_canvas.draw()

    # ── TABLE TAB ───────────────────────────
    def _build_table_tab(self):
        cols = ["Date", "Time", "Name", "Number", "Call Type", "Duration(m)"]
        style = ttk.Style()
        style.configure("Treeview", background=CARD, foreground=TEXT,
                        fieldbackground=CARD, rowheight=26,
                        font=("Courier New", 9))
        style.configure("Treeview.Heading", background="#0d1525", foreground=ACCENT,
                        font=("Courier New", 9, "bold"))
        style.map("Treeview", background=[("selected", ACCENT)])

        frame = tk.Frame(self.tab_table, bg=BG)
        frame.pack(fill="both", expand=True, padx=8, pady=8)

        self.tree = ttk.Treeview(frame, columns=cols, show="headings", selectmode="browse")
        for col in cols:
            w = 130 if col == "Name" else 110
            self.tree.heading(col, text=col,
                              command=lambda c=col: self._sort_tree(c))
            self.tree.column(col, width=w, anchor="center")

        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.tree.tag_configure("Incoming", foreground=GREEN)
        self.tree.tag_configure("Outgoing", foreground=ORANGE)
        self.tree.tag_configure("Missed",   foreground=RED)

        self._populate_table()

    def _populate_table(self):
        self.tree.delete(*self.tree.get_children())
        for _, row in self.filtered_df.iterrows():
            tag = row["Call Type"]
            dur = f"{row['Duration(m)']:.2f}" if row["Call Type"] != "Missed" else "—"
            self.tree.insert("", "end", values=(
                row["Date"], row["Time"], row["Name"],
                row["Number"], row["Call Type"], dur
            ), tags=(tag,))

    def _sort_tree(self, col):
        data = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]
        try:
            data.sort(key=lambda x: float(x[0].replace("—", "0")))
        except ValueError:
            data.sort()
        for i, (_, k) in enumerate(data):
            self.tree.move(k, "", i)

    # ── SUMMARY TAB ─────────────────────────
    def _build_summary_tab(self):
        self.summary_text = tk.Text(self.tab_summary, bg=CARD, fg=TEXT,
                                    font=("Courier New", 11),
                                    relief="flat", padx=20, pady=20,
                                    state="disabled", wrap="word")
        self.summary_text.pack(fill="both", expand=True, padx=8, pady=8)
        self._update_summary()

    def _update_summary(self):
        df = self.filtered_df
        total       = len(df)
        incoming    = len(df[df["Call Type"] == "Incoming"])
        outgoing    = len(df[df["Call Type"] == "Outgoing"])
        missed      = len(df[df["Call Type"] == "Missed"])
        avg_dur     = df[df["Call Type"] != "Missed"]["Duration(m)"].mean()
        top_contact = df[df["Call Type"] != "Missed"].groupby("Name")["Duration(m)"].sum().idxmax()
        busiest_day = df.groupby("Date").size().idxmax()
        peak_hour   = pd.to_datetime(df["Time"], infer_datetime_format=True, errors="coerce").dt.hour.mode()[0]

        text = f"""
╔══════════════════════════════════════════════╗
║         CDR ANALYSIS SUMMARY REPORT         ║
╚══════════════════════════════════════════════╝

📊  OVERALL STATISTICS
─────────────────────────────────────────
  Total Calls Recorded  :  {total}
  Incoming Calls        :  {incoming}  ({incoming/total*100:.1f}%)
  Outgoing Calls        :  {outgoing}  ({outgoing/total*100:.1f}%)
  Missed Calls          :  {missed}  ({missed/total*100:.1f}%)
  Unique Contacts       :  {df['Name'].nunique()}

⏱️  DURATION ANALYSIS
─────────────────────────────────────────
  Average Call Duration :  {avg_dur:.2f} minutes
  Total Talk Time       :  {df['Duration(m)'].sum():.1f} minutes
  Longest Call          :  {df['Duration(m)'].max():.2f} minutes
  Shortest Call (non-0) :  {df[df['Duration(m)']>0]['Duration(m)'].min():.2f} minutes

🏆  TOP INSIGHTS
─────────────────────────────────────────
  Most Talked Contact   :  {top_contact}
  Busiest Day           :  {busiest_day}
  Peak Call Hour        :  {peak_hour:02d}:00 – {peak_hour+1:02d}:00

📅  DATE RANGE
─────────────────────────────────────────
  From  :  {df['Date'].min()}
  To    :  {df['Date'].max()}

════════════════════════════════════════════
  Report generated on {datetime.now().strftime("%d %b %Y, %I:%M %p")}
════════════════════════════════════════════
"""
        self.summary_text.config(state="normal")
        self.summary_text.delete("1.0", "end")
        self.summary_text.insert("1.0", text)
        self.summary_text.config(state="disabled")

    # ── STAT CARDS ──────────────────────────
    def _update_stats(self):
        df = self.filtered_df
        total    = len(df)
        incoming = len(df[df["Call Type"] == "Incoming"])
        outgoing = len(df[df["Call Type"] == "Outgoing"])
        missed   = len(df[df["Call Type"] == "Missed"])
        avg_dur  = df[df["Call Type"] != "Missed"]["Duration(m)"].mean()
        contacts = df["Name"].nunique()

        self.stat_labels["total"].config(text=str(total))
        self.stat_labels["incoming"].config(text=str(incoming))
        self.stat_labels["outgoing"].config(text=str(outgoing))
        self.stat_labels["missed"].config(text=str(missed))
        self.stat_labels["duration"].config(text=f"{avg_dur:.1f} min")
        self.stat_labels["contacts"].config(text=str(contacts))

    # ── ACTIONS ─────────────────────────────
    def _apply_filter(self):
        df = self.df.copy()
        ct = self.filter_type.get()
        cn = self.filter_contact.get()
        if ct != "All":
            df = df[df["Call Type"] == ct]
        if cn != "All":
            df = df[df["Name"] == cn]
        self.filtered_df = df
        self._update_stats()
        self._draw_all_charts()
        self._populate_table()
        self._update_summary()

    def _refresh(self):
        self.df = generate_dummy_cdr(200)
        self.filtered_df = self.df.copy()
        self.filter_type.set("All")
        self.filter_contact.set("All")
        self._update_stats()
        self._draw_all_charts()
        self._populate_table()
        self._update_summary()
        messagebox.showinfo("Refreshed", "New dummy CDR data generated!")

    def _load_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if not path:
            return
        try:
            df = pd.read_csv(path)

            # ── Normalise column names (strip spaces and trailing colons) ───
            df.columns = df.columns.str.strip()
            col_lower = {c.lower().rstrip(":"): c for c in df.columns}

            rename_map = {}
            if "name" in col_lower and "Name" not in df.columns:
                rename_map[col_lower["name"]] = "Name"
            if "type" in col_lower and "Call Type" not in df.columns:
                rename_map[col_lower["type"]] = "Call Type"
            if "duration" in col_lower and "Duration(s)" not in df.columns:
                rename_map[col_lower["duration"]] = "Duration(s)"
            if "number" in col_lower and "Number" not in df.columns:
                rename_map[col_lower["number"]] = "Number"
            df.rename(columns=rename_map, inplace=True)

            # ── Validate required columns ───────────────────────────────────
            required = {"Date", "Time", "Name", "Number", "Call Type", "Duration(s)"}
            missing = required - set(df.columns)
            if missing:
                messagebox.showerror("Error",
                    f"CSV is missing columns:\n{', '.join(missing)}\n\n"
                    f"Found: {', '.join(df.columns)}")
                return

            # ── Fix Call Type typo: 'Incomming' → 'Incoming' ───────────────
            df["Call Type"] = df["Call Type"].str.strip().replace({"Incomming": "Incoming"})

            # ── Parse Duration: handles '40 sec', '1761 sec', or plain int ──
            def parse_dur(val):
                if pd.isna(val):
                    return 0
                s = str(val).strip().lower().replace("sec", "").strip()
                try:
                    return int(float(s))
                except ValueError:
                    return 0

            df["Duration(s)"] = df["Duration(s)"].apply(parse_dur)
            df["Duration(m)"] = df["Duration(s)"] / 60

            # ── Parse DateTime ──────────────────────────────────────────────
            df["Time"] = df["Time"].astype(str).str.strip()
            df["DateTime"] = pd.to_datetime(
                df["Date"] + " " + df["Time"], infer_datetime_format=True, errors="coerce")
            df["Week"]  = pd.to_datetime(df["Date"], errors="coerce").dt.isocalendar().week.astype(str)
            df["Month"] = pd.to_datetime(df["Date"], errors="coerce").dt.strftime("%b")

            self.df = df
            self.filtered_df = df.copy()

            names = ["All"] + sorted(df["Name"].dropna().unique().tolist())
            self.filter_contact["values"] = names
            self.filter_contact.set("All")
            call_types = ["All"] + sorted(df["Call Type"].dropna().unique().tolist())
            self.filter_type["values"] = call_types
            self.filter_type.set("All")

            self._update_stats()
            self._draw_all_charts()
            self._populate_table()
            self._update_summary()
            messagebox.showinfo("Loaded", f"Loaded {len(df)} records from CSV!")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                                            filetypes=[("CSV", "*.csv")])
        if path:
            cols = ["Date", "Time", "Name", "Number", "Call Type", "Duration(s)", "Duration(m)"]
            self.filtered_df[cols].to_csv(path, index=False)
            messagebox.showinfo("Exported", f"Data saved to:\n{path}")


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app  = CDRAnalyzerApp(root)
    root.mainloop()
