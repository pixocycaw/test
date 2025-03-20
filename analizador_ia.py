import re
import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import webbrowser
import threading
from collections import Counter
import requests
from urllib.parse import quote_plus
import json
import time
import math

# Clase que analiza la fiabilidad de respuestas generadas por IA
class AIReliabilityChecker:
    def __init__(self):
        # Frases que indican incertidumbre
        self.uncertain_phrases = [
            "podría", "parece", "se cree", "es posible", "probablemente", 
            "algunas personas dicen", "puede ser", "quizás", "tal vez", 
            "supuestamente", "según algunos", "no está claro", "se especula"
        ]
        
        # Pares de palabras contradictorias
        self.contradictory_pairs = [
            ("sí", "no"), ("verdadero", "falso"), ("positivo", "negativo"),
            ("siempre", "nunca"), ("todos", "ninguno"), ("debe", "no debe"),
            ("correcto", "incorrecto"), ("cierto", "incierto")
        ]
        
        # Operadores y palabras clave matemáticas para detectar expresiones
        self.math_operators = ['+', '-', '*', '/', '=', '<', '>', '≤', '≥', '²', '³', '√']
        self.math_keywords = ['suma', 'resta', 'multiplica', 'divide', 'igual', 'ecuación', 
                            'porcentaje', 'promedio', 'media', 'probabilidad', 'estadística',
                            'raíz cuadrada', 'exponente', 'logaritmo', 'derivada', 'integral']
    
    # Divide el texto en oraciones
    def sentence_tokenize(self, text):
        # Protege abreviaturas comunes
        text = re.sub(r'(Sr\.|Dr\.|Sra\.|etc\.)', lambda m: m.group().replace('.', '<DOT>'), text)
        
        # Divide por puntos, signos de exclamación o interrogación
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Restaura los puntos en las abreviaturas
        sentences = [s.replace('<DOT>', '.') for s in sentences]
        
        # Elimina oraciones vacías
        sentences = [s for s in sentences if s.strip()]
        
        return sentences
    
    # Analiza el nivel de certeza contando frases de incertidumbre
    def analyze_certainty(self, response):
        count = sum(1 for phrase in self.uncertain_phrases if phrase in response.lower())
        return count
    
    # Busca URLs y citas en el texto
    def check_references(self, response):
        urls = re.findall(r'https?://\S+|www\.\S+', response)
        citations = re.findall(r'\[\d+\]|\(\d{4}\)', response)
        return len(urls) + len(citations)
    
    # Verifica la coherencia buscando contradicciones y cambios de tema
    def check_coherence(self, response):
        words = response.lower().split()
        counter = Counter(words)
        
        # Cuenta contradicciones
        contradictions = sum(1 for a, b in self.contradictory_pairs 
                             if counter[a] > 0 and counter[b] > 0)
        
        sentences = self.sentence_tokenize(response)
        if len(sentences) <= 1:
            return contradictions
        
        # Detecta cambios bruscos de tema entre oraciones
        topic_shifts = 0
        for i in range(1, len(sentences)):
            prev_words = set(sentences[i-1].lower().split())
            curr_words = set(sentences[i].lower().split())
            common_words = prev_words.intersection(curr_words)
            if len(common_words) <= 1 and len(prev_words) > 3 and len(curr_words) > 3:
                topic_shifts += 1
                
        return contradictions + (topic_shifts * 0.5)
    
    # Analiza inconsistencias factuales, especialmente con fechas y números
    def analyze_factual_consistency(self, response):
        sentences = self.sentence_tokenize(response)
        
        date_pattern = r'\b\d{1,2}/\d{1,2}/\d{2,4}|\d{4}\b'
        number_pattern = r'\b\d+[.,]?\d*\s*%?\b'
        
        inconsistencies = 0
        numbers = []
        
        # Busca números en el texto
        for sentence in sentences:
            found_numbers = re.findall(number_pattern, sentence)
            numbers.extend(found_numbers)
        
        # Verifica inconsistencias numéricas    
        number_counter = Counter(numbers)
        if len(number_counter) > 0 and max(number_counter.values()) > 1:
            inconsistencies += 1
            
        return inconsistencies
    
    # Extrae expresiones matemáticas del texto
    def extract_math_expressions(self, text):
        # Operaciones aritméticas básicas
        basic_arithmetic = re.findall(r'\b\d+\s*[\+\-\*/]\s*\d+\s*=\s*\d+[.,]?\d*\b', text)
        
        # Cálculos de porcentaje
        percentages = re.findall(r'\b\d+[.,]?\d*\s*%\s*(?:de|of)?\s*\d+[.,]?\d*\s*=\s*\d+[.,]?\d*\b', text)
        
        # Ecuaciones simples
        equations = re.findall(r'\b[xyz]\s*=\s*\d+[.,]?\d*\b|\b\d+[xyz]\s*[\+\-\*/]\s*\d+[.,]?\d*\s*=\s*\d+[.,]?\d*\b', text)
        
        # Busca oraciones que contienen lenguaje matemático
        statements = []
        sentences = self.sentence_tokenize(text)
        
        for sentence in sentences:
            has_math_keyword = any(keyword in sentence.lower() for keyword in self.math_keywords)
            has_operator = any(op in sentence for op in self.math_operators)
            has_numbers = len(re.findall(r'\b\d+[.,]?\d*\b', sentence)) >= 2
            
            if (has_math_keyword or has_operator) and has_numbers:
                statements.append(sentence)
        
        return basic_arithmetic + percentages + equations + statements
    
    # Verifica operaciones aritméticas básicas
    def verify_basic_arithmetic(self, expression):
        try:
            match = re.search(r'(\d+[.,]?\d*)\s*([\+\-\*/])\s*(\d+[.,]?\d*)\s*=\s*(\d+[.,]?\d*)', expression)
            if not match:
                return None
                
            num1 = float(match.group(1).replace(',', '.'))
            operator = match.group(2)
            num2 = float(match.group(3).replace(',', '.'))
            result = float(match.group(4).replace(',', '.'))
            
            # Calcula el resultado esperado según el operador
            expected = None
            if operator == '+':
                expected = num1 + num2
            elif operator == '-':
                expected = num1 - num2
            elif operator == '*':
                expected = num1 * num2
            elif operator == '/':
                if num2 == 0:
                    return False
                expected = num1 / num2
            
            # Compara con margen de error
            return abs(expected - result) < 0.01
            
        except Exception:
            return None
    
    # Verifica cálculos de porcentaje
    def verify_percentage(self, expression):
        try:
            match = re.search(r'(\d+[.,]?\d*)\s*%\s*(?:de|of)?\s*(\d+[.,]?\d*)\s*=\s*(\d+[.,]?\d*)', expression)
            if not match:
                return None
                
            percentage = float(match.group(1).replace(',', '.'))
            base = float(match.group(2).replace(',', '.'))
            result = float(match.group(3).replace(',', '.'))
            
            expected = (percentage / 100) * base
            
            return abs(expected - result) < 0.01
            
        except Exception:
            return None
    
    # Evalúa la precisión matemática del texto
    def check_math_accuracy(self, response):
        expressions = self.extract_math_expressions(response)
        if not expressions:
            return {"detected": 0, "errors": 0, "accuracy": None}
            
        error_count = 0
        verified_count = 0
        
        math_errors = []
        
        # Verifica cada expresión matemática
        for expr in expressions:
            is_valid = None
            
            if is_valid is None:
                is_valid = self.verify_basic_arithmetic(expr)
                
            if is_valid is None:
                is_valid = self.verify_percentage(expr)
            
            if is_valid is not None:
                verified_count += 1
                if is_valid is False:
                    error_count += 1
                    math_errors.append(expr)
        
        # Calcula la precisión matemática
        accuracy = None
        if verified_count > 0:
            accuracy = ((verified_count - error_count) / verified_count) * 100
            
        return {
            "detected": len(expressions),
            "verified": verified_count,
            "errors": error_count,
            "accuracy": accuracy,
            "error_examples": math_errors[:3]
        }
    
    # Simulación de búsqueda web (placeholder, para implementar)
    def search_web(self, query, num_results=3):
        """
        TODO contrastar con busquedas
        """
        try:
            time.sleep(0.5)
            return [
                f"https://example.com/result1?q={quote_plus(query)}",
                f"https://example.com/result2?q={quote_plus(query)}",
                f"https://example.com/result3?q={quote_plus(query)}"
            ][:num_results]
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    # Analiza la legibilidad del texto
    def analyze_readability(self, response):
        sentences = self.sentence_tokenize(response)
        if not sentences:
            return 0
            
        words = response.split()
        if not words:
            return 0
            
        # Promedio de palabras por oración y longitud de palabras
        avg_words = len(words) / len(sentences)
        avg_word_length = sum(len(word) for word in words) / len(words)
        
        readability = (avg_words * 0.3) + (avg_word_length * 0.5)
        
        return round(readability, 1)
    
    # Evalúa la respuesta y calcula un puntaje de fiabilidad
    def evaluate_response(self, response):
        if not response.strip():
            return {"Puntaje de fiabilidad": 0}
        
        # Recopila métricas
        certainty_score = self.analyze_certainty(response)
        references_count = self.check_references(response)
        coherence_issues = self.check_coherence(response)
        factual_inconsistencies = self.analyze_factual_consistency(response)
        readability_score = self.analyze_readability(response)
        math_check = self.check_math_accuracy(response)
        
        # Busca resultados web relacionados
        main_topic = response.split('.')[0] if '.' in response else response[:100]
        search_results = self.search_web(main_topic)
        
        # Calcula el puntaje de fiabilidad
        base_score = 100
        
        uncertainty_deduction = certainty_score * 5
        coherence_deduction = coherence_issues * 10
        factual_deduction = factual_inconsistencies * 15
        
        math_deduction = 0
        if math_check["accuracy"] is not None:
            if math_check["errors"] > 0:
                error_rate = math_check["errors"] / math_check["verified"]
                math_deduction = error_rate * 25
        
        readability_adjustment = 0
        if readability_score < 3:
            readability_adjustment = -5
        elif readability_score > 10:
            readability_adjustment = -5
        
        reference_bonus = min(references_count * 5, 15)
        
        reliability_score = (base_score - uncertainty_deduction - coherence_deduction - 
                           factual_deduction - math_deduction + reference_bonus + readability_adjustment)
        reliability_score = max(0, min(100, round(reliability_score, 1)))
        
        math_accuracy = str(round(math_check["accuracy"], 1)) + "%" if math_check["accuracy"] is not None else "N/A"
        
        # Devuelve los resultados
        return {
            "Certeza (menos es mejor)": certainty_score,
            "Referencias encontradas": references_count,
            "Problemas de coherencia": coherence_issues,
            "Inconsistencias factuales": factual_inconsistencies,
            "Expresiones matemáticas": math_check["detected"],
            "Verificadas matemáticamente": math_check["verified"],
            "Errores matemáticos": math_check["errors"],
            "Precisión matemática": math_accuracy,
            "Complejidad del texto": readability_score,
            "Resultados web relevantes": search_results,
            "Ejemplos de errores matemáticos": math_check["error_examples"],
            "Puntaje de fiabilidad": reliability_score
        }


# Clase que implementa la interfaz gráfica
class AIReliabilityCheckerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Analizador de Fiabilidad de IA")
        self.root.geometry("700x700")
        
        self.checker = AIReliabilityChecker()
        self.create_ui()
    
    # Crea la UI
    def create_ui(self):
        main_frame = tk.Frame(self.root, padx=15, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Área para ingresar texto
        input_frame = tk.LabelFrame(main_frame, text="Respuesta de IA", padx=10, pady=10)
        input_frame.pack(fill=tk.BOTH, expand=True)
        
        self.text_area = scrolledtext.ScrolledText(input_frame, wrap=tk.WORD, width=60, height=10)
        self.text_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Botones
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.analyze_button = tk.Button(button_frame, text="Analizar", command=self.start_analysis, 
                                        bg="#4CAF50", fg="white", padx=10, pady=5)
        self.analyze_button.pack(side=tk.LEFT, padx=5)
        
        self.clear_button = tk.Button(button_frame, text="Limpiar", command=self.clear_text,
                                     bg="#f44336", fg="white", padx=10, pady=5)
        self.clear_button.pack(side=tk.LEFT, padx=5)
        
        self.sample_button = tk.Button(button_frame, text="Texto Ejemplo", 
                                      command=self.load_sample_text,
                                      bg="#2196F3", fg="white", padx=10, pady=5)
        self.sample_button.pack(side=tk.LEFT, padx=5)
        
        self.math_sample_button = tk.Button(button_frame, text="Ejemplo Matemático", 
                                           command=self.load_math_sample,
                                           bg="#9C27B0", fg="white", padx=10, pady=5)
        self.math_sample_button.pack(side=tk.LEFT, padx=5)
        
        # Marco de resultados
        results_frame = tk.LabelFrame(main_frame, text="Resultados", padx=10, pady=10)
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        # Puntaje de fiabilidad
        score_frame = tk.Frame(results_frame)
        score_frame.pack(fill=tk.X, pady=5)
        
        self.score_label = tk.Label(score_frame, text="Puntaje de Fiabilidad: -", 
                                    font=("Arial", 12, "bold"))
        self.score_label.pack(side=tk.LEFT, padx=5)
        
        # Barra de progreso
        self.progress_frame = tk.Frame(results_frame)
        self.progress_frame.pack(fill=tk.X, pady=5)
        
        self.progress_bar = ttk.Progressbar(self.progress_frame, length=300, mode='determinate')
        self.progress_bar.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Pestañas para mostrar métricas
        self.results_notebook = ttk.Notebook(results_frame)
        self.results_notebook.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Pestaña de métricas generales
        self.metrics_tab = tk.Frame(self.results_notebook)
        self.results_notebook.add(self.metrics_tab, text="Métricas Generales")
        self.metrics_frame = tk.Frame(self.metrics_tab)
        self.metrics_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Pestaña de análisis matemático
        self.math_tab = tk.Frame(self.results_notebook)
        self.results_notebook.add(self.math_tab, text="Análisis Matemático")
        self.math_frame = tk.Frame(self.math_tab)
        self.math_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.math_errors_frame = tk.Frame(self.math_tab)
        self.math_errors_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Marco para enlaces
        self.links_frame = tk.Frame(results_frame)
        self.links_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Barra de estado
        self.status_var = tk.StringVar()
        self.status_var.set("Listo")
        self.status_bar = tk.Label(self.root, textvariable=self.status_var, 
                                  bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    # Carga un texto de ejemplo
    def load_sample_text(self):
        sample_text = (
            "La inteligencia artificial podría revolucionar varios campos en el futuro. "
            "Algunos expertos dicen que reemplazará muchos trabajos, mientras que otros creen "
            "que creará nuevas oportunidades. En 2022, el mercado de IA alcanzó $62 mil millones, "
            "y se predice que en 2025 superará los $100 mil millones. Google y Microsoft han "
            "invertido fuertemente en esta tecnología. La IA es definitivamente buena para la sociedad, "
            "aunque también podría ser perjudicial en algunos aspectos. "
            "Todos los países deberían adoptar regulaciones estrictas, pero ningún país "
            "debería limitar la investigación."
        )
        self.text_area.delete("1.0", tk.END)
        self.text_area.insert("1.0", sample_text)
    
    # Carga un ejemplo con contenido matemático
    def load_math_sample(self):
        math_sample = (
            "El impacto económico de la IA se puede calcular de la siguiente manera. "
            "Si una empresa invierte $50,000 en tecnología de IA y esto aumenta su productividad en un 15%, "
            "para una empresa con ingresos de $2,000,000, esto representa un aumento de $300,000. "
            "El retorno de inversión sería 300,000 / 50,000 = 6, o 600%. "
            "En promedio, las empresas ven un aumento del 22% en su productividad. "
            "La fórmula para calcular el retorno es: 2,000,000 * 0.15 = 300,000. "
            "Si consideramos los costos operativos, que son 25% de los ingresos, tenemos "
            "2,000,000 * 0.25 = 500,000 en costos. "
            "El margen de beneficio después de la implementación será: "
            "(2,000,000 + 300,000 - 500,000) / 2,300,000 = 0.78 o 78%. "
            "Si 5 + 7 = 12, entonces podemos decir que la suma de los costos de implementación "
            "y mantenimiento (5,000 + 7,000 = 13,000) afectará el primer año de retorno. "
            "La raíz cuadrada de 144 es 12, lo que representa los meses necesarios para recuperar la inversión."
        )
        self.text_area.delete("1.0", tk.END)
        self.text_area.insert("1.0", math_sample)
    
    # Limpia el área de texto
    def clear_text(self):
        self.text_area.delete("1.0", tk.END)
    
    # Inicia el análisis en un hilo separado
    def start_analysis(self):
        response = self.text_area.get("1.0", tk.END).strip()
        if not response:
            messagebox.showwarning("Advertencia", "Ingresa una respuesta para analizar.")
            return
        
        self.analyze_button.config(state=tk.DISABLED)
        self.status_var.set("Analizando...")
        
        thread = threading.Thread(target=self.analyze_text, args=(response,))
        thread.daemon = True
        thread.start()
    
    # Realiza el análisis del texto
    def analyze_text(self, response):
        try:
            result = self.checker.evaluate_response(response)
            
            self.root.after(0, lambda: self.update_results(result))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Error al analizar: {str(e)}"))
        finally:
            self.root.after(0, lambda: self.analyze_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.status_var.set("Análisis completado"))
    
    # Actualiza la interfaz con los resultados
    def update_results(self, result):
        # Actualiza el puntaje y la barra de progreso
        score = result["Puntaje de fiabilidad"]
        self.score_label.config(text=f"Puntaje de Fiabilidad: {score}")
        self.progress_bar["value"] = score
        
        # Asigna color según el puntaje
        if score >= 70:
            color = "#4CAF50"  # Verde
        elif score >= 40:
            color = "#FF9800"  # Naranja
        else:
            color = "#f44336"  # Rojo
        
        self.score_label.config(fg=color)
        
        # Limpia y actualiza el panel de métricas generales
        for widget in self.metrics_frame.winfo_children():
            widget.destroy()
        
        metrics_to_display = {k: v for k, v in result.items() 
                             if k not in ["Resultados web relevantes", "Puntaje de fiabilidad", 
                                         "Ejemplos de errores matemáticos"] and 
                                not k.startswith("Expres") and not k.startswith("Verifi") and 
                                not k.startswith("Error") and not k.startswith("Precis")}
        
        row = 0
        for key, value in metrics_to_display.items():
            tk.Label(self.metrics_frame, text=f"{key}:", anchor="w").grid(row=row, column=0, sticky="w", padx=5, pady=2)
            tk.Label(self.metrics_frame, text=str(value)).grid(row=row, column=1, sticky="w", padx=5, pady=2)
            row += 1
        
        # Limpia y actualiza el panel de métricas matemáticas
        for widget in self.math_frame.winfo_children():
            widget.destroy()
            
        math_metrics = {k: v for k, v in result.items() 
                       if k.startswith("Expres") or k.startswith("Verifi") or 
                          k.startswith("Error") or k.startswith("Precis")}
        
        row = 0
        for key, value in math_metrics.items():
            tk.Label(self.math_frame, text=f"{key}:", anchor="w").grid(row=row, column=0, sticky="w", padx=5, pady=2)
            tk.Label(self.math_frame, text=str(value)).grid(row=row, column=1, sticky="w", padx=5, pady=2)
            row += 1
            
        # Muestra ejemplos de errores matemáticos
        for widget in self.math_errors_frame.winfo_children():
            widget.destroy()
            
        math_errors = result.get("Ejemplos de errores matemáticos", [])
        if math_errors:
            tk.Label(self.math_errors_frame, text="Ejemplos de errores matemáticos detectados:", 
                    font=("Arial", 10, "bold")).pack(anchor="w", pady=5)
            
            for i, error in enumerate(math_errors, 1):
                tk.Label(self.math_errors_frame, text=f"{i}. {error}", 
                        fg="red", wraplength=500).pack(anchor="w", pady=2)
        else:
            tk.Label(self.math_errors_frame, text="No se detectaron errores matemáticos", 
                    fg="green").pack(anchor="w", pady=5)
        
        # Selecciona la pestaña adecuada
        if result.get("Expresiones matemáticas", 0) > 0:
            self.results_notebook.select(1)  # Pestaña matemática
        else:
            self.results_notebook.select(0)  # Pestaña general
        
        # Muestra los enlaces web
        for widget in self.links_frame.winfo_children():
            widget.destroy()
        
        if result["Resultados web relevantes"]:
            tk.Label(self.links_frame, text="Fuentes encontradas:", 
                    font=("Arial", 10, "bold")).pack(anchor="w", pady=5)
            
            for url in result["Resultados web relevantes"]:
                link = tk.Label(self.links_frame, text=url, fg="blue", cursor="hand2")
                link.pack(anchor="w", pady=2)
                link.bind("<Button-1>", lambda e, u=url: webbrowser.open(u))


# Función principal para iniciar la aplicación
def main():
    try:
        root = tk.Tk()
        app = AIReliabilityCheckerApp(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Error", f"Error al iniciar la aplicación: {str(e)}")


# Punto de entrada de la aplicación
if __name__ == "__main__":
    main()