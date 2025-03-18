import re
import requests
from googlesearch import search
from collections import Counter
import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import webbrowser

def analyze_certainty(response):
    uncertain_words = ["podría", "parece", "se cree", "es posible", "probablemente", "algunas personas dicen"]
    count = sum(1 for word in uncertain_words if word in response.lower())
    return count

def check_references(response):
    return bool(re.search(r'https?://\S+|www\.\S+', response))

def check_coherence(response):
    words = response.lower().split()
    counter = Counter(words)
    contradictory_pairs = [("sí", "no"), ("verdadero", "falso"), ("positivo", "negativo")]
    contradictions = sum(1 for a, b in contradictory_pairs if counter[a] > 0 and counter[b] > 0)
    return contradictions

def search_web(query, num_results=3):
    try:
        return [url for url in search(query, num_results=num_results)]
    except Exception as e:
        return []

def evaluate_response(response):
    certainty_score = analyze_certainty(response)
    has_references = check_references(response)
    coherence_issues = check_coherence(response)
    
    search_results = search_web(response[:100])  # Busca solo los primeros 100 caracteres
    
    reliability_score = 100 - (certainty_score * 10 + coherence_issues * 15)
    reliability_score = max(0, min(100, reliability_score))  # Mantener entre 0 y 100
    
    return {
        "Certeza (menos es mejor)": certainty_score,
        "Contiene referencias": has_references,
        "Problemas de coherencia": coherence_issues,
        "Resultados web relevantes": search_results,
        "Puntaje de fiabilidad": reliability_score
    }

def analyze_text():
    response = text_area.get("1.0", tk.END).strip()
    if not response:
        messagebox.showwarning("Advertencia", "Ingresa una respuesta para analizar.")
        return
    result = evaluate_response(response)
    
    score = result["Puntaje de fiabilidad"]
    progress_bar["value"] = score
    score_label.config(text=f"Puntaje de Fiabilidad: {score}")
    
    links_frame.pack_forget()
    for widget in links_frame.winfo_children():
        widget.destroy()
    
    if result["Resultados web relevantes"]:
        tk.Label(links_frame, text="Fuentes encontradas:", font=("Arial", 10, "bold")).pack(anchor="w")
        for url in result["Resultados web relevantes"]:
            link = tk.Label(links_frame, text=url, fg="blue", cursor="hand2")
            link.pack(anchor="w")
            link.bind("<Button-1>", lambda e, u=url: webbrowser.open(u))
        links_frame.pack()

# Crear la interfaz gráfica
root = tk.Tk()
root.title("Analizador de Fiabilidad de IA")

frame = tk.Frame(root, padx=10, pady=10)
frame.pack(padx=10, pady=10)

label = tk.Label(frame, text="Ingresa la respuesta de la IA:")
label.pack()

text_area = scrolledtext.ScrolledText(frame, width=60, height=10)
text_area.pack()

button = tk.Button(frame, text="Analizar", command=analyze_text)
button.pack(pady=5)

score_label = tk.Label(frame, text="Puntaje de Fiabilidad: -", font=("Arial", 12, "bold"))
score_label.pack()

progress_bar = ttk.Progressbar(frame, length=200, mode='determinate')
progress_bar.pack(pady=5)

links_frame = tk.Frame(frame)

root.mainloop()