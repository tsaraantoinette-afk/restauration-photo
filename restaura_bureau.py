"""
Restaura — interface graphique de bureau (Tkinter) pour améliorer les photos localement.

Utilise la même chaîne OpenCV / NumPy que le serveur (serveur/restauration.py) :
pastilles, inpainting, filtre bilatéral, LAB + CLAHE, masque de netteté. Toujours en couleur.

Installation : pip install opencv-python-headless numpy pillow
Lancement   : python restaura_bureau.py
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import cv2
from PIL import Image, ImageTk

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "serveur"))
from restauration import restaurer  # noqa: E402

FORMATS = [("Images", "*.jpg *.jpeg *.png *.bmp *.tif *.tiff *.webp"), ("Tous", "*.*")]


class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Restaura — Amélioration de photos")
        self.geometry("1100x680")
        self.minsize(760, 480)
        self.configure(bg="#1f2a24")
        self.originale = None
        self.resultat = None
        self.chemin = None
        self._apercus = {}

        barre = tk.Frame(self, bg="#1f2a24")
        barre.pack(fill="x", padx=12, pady=10)
        style = {"bg": "#f3efe4", "fg": "#1f2a24", "relief": "flat", "padx": 14, "pady": 6,
                 "font": ("Georgia", 11), "cursor": "hand2"}
        tk.Button(barre, text="Ouvrir une photo", command=self.ouvrir, **style).pack(side="left")
        self.btn_ameliorer = tk.Button(barre, text="Améliorer", command=self.ameliorer,
                                       state="disabled", **style)
        self.btn_ameliorer.pack(side="left", padx=8)
        self.btn_enregistrer = tk.Button(barre, text="Enregistrer", command=self.enregistrer,
                                         state="disabled", **style)
        self.btn_enregistrer.pack(side="left")
        self.progression = ttk.Progressbar(barre, mode="indeterminate", length=160)
        self.progression.pack(side="right")

        zone = tk.Frame(self, bg="#1f2a24")
        zone.pack(fill="both", expand=True, padx=12)
        zone.columnconfigure((0, 1), weight=1, uniform="c")
        zone.rowconfigure(1, weight=1)
        for col, titre in enumerate(("Avant", "Après")):
            tk.Label(zone, text=titre, bg="#1f2a24", fg="#f3efe4",
                     font=("Georgia", 13, "italic")).grid(row=0, column=col, pady=(0, 6))
        self.cadre_avant = tk.Label(zone, bg="#2b3830", text="Aucune image", fg="#9aa59c")
        self.cadre_apres = tk.Label(zone, bg="#2b3830", text="", fg="#9aa59c")
        self.cadre_avant.grid(row=1, column=0, sticky="nsew", padx=(0, 6))
        self.cadre_apres.grid(row=1, column=1, sticky="nsew", padx=(6, 0))

        self.statut = tk.StringVar(value="Ouvrez une photo pour commencer.")
        tk.Label(self, textvariable=self.statut, bg="#1f2a24", fg="#c9c2b0",
                 anchor="w", font=("Helvetica", 10)).pack(fill="x", padx=12, pady=8)
        self.bind("<Configure>", lambda e: self.after_idle(self.rafraichir))

    def afficher(self, cadre, img_bgr, cle):
        if img_bgr is None:
            return
        cadre.update_idletasks()
        lw, lh = max(cadre.winfo_width(), 50), max(cadre.winfo_height(), 50)
        pil = Image.fromarray(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))
        pil.thumbnail((lw - 8, lh - 8))
        self._apercus[cle] = ImageTk.PhotoImage(pil)
        cadre.configure(image=self._apercus[cle], text="")

    def rafraichir(self):
        self.afficher(self.cadre_avant, self.originale, "avant")
        self.afficher(self.cadre_apres, self.resultat, "apres")

    def ouvrir(self):
        chemin = filedialog.askopenfilename(title="Choisir une photo", filetypes=FORMATS)
        if not chemin:
            return
        img = cv2.imread(chemin, cv2.IMREAD_COLOR)
        if img is None:
            messagebox.showerror("Restaura", "Cette image est illisible.")
            return
        self.chemin, self.originale, self.resultat = chemin, img, None
        self.cadre_apres.configure(image="", text="")
        self.btn_ameliorer.configure(state="normal")
        self.btn_enregistrer.configure(state="disabled")
        self.statut.set(f"{os.path.basename(chemin)} — {img.shape[1]}×{img.shape[0]} px")
        self.rafraichir()

    def ameliorer(self):
        self.btn_ameliorer.configure(state="disabled")
        self.progression.start(12)
        self.statut.set("Amélioration en cours (pastille par pastille)…")

        def tache():
            try:
                res, rapport = restaurer(self.originale.copy())
                self.after(0, self.fini, res, rapport, None)
            except Exception as e:  # noqa: BLE001
                self.after(0, self.fini, None, None, e)

        threading.Thread(target=tache, daemon=True).start()

    def fini(self, res, rapport, erreur):
        self.progression.stop()
        self.btn_ameliorer.configure(state="normal")
        if erreur:
            messagebox.showerror("Restaura", f"L'amélioration a échoué : {erreur}")
            self.statut.set("Échec de l'amélioration.")
            return
        self.resultat = res
        self.btn_enregistrer.configure(state="normal")
        self.statut.set(
            f"Terminé — {rapport['pastilles']} pastilles analysées, "
            f"{rapport['taux_degats']} % de défauts reconstruits."
        )
        self.rafraichir()

    def enregistrer(self):
        base = os.path.splitext(os.path.basename(self.chemin or "photo"))[0]
        chemin = filedialog.asksaveasfilename(
            title="Enregistrer la photo améliorée", defaultextension=".jpg",
            initialfile=f"{base}-ameliore.jpg",
            filetypes=[("JPEG", "*.jpg"), ("PNG", "*.png")])
        if not chemin:
            return
        params = [cv2.IMWRITE_JPEG_QUALITY, 95] if chemin.lower().endswith((".jpg", ".jpeg")) else []
        if cv2.imwrite(chemin, self.resultat, params):
            self.statut.set(f"Enregistré : {chemin}")
        else:
            messagebox.showerror("Restaura", "Impossible d'enregistrer le fichier.")


if __name__ == "__main__":
    Application().mainloop()
