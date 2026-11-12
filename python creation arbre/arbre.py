import tkinter as tk
import random
import itertools

class DestructibleNetwork:
    def __init__(self, root):
        self.root = root
        self.root.title("Réseau Destructible")
        
        # Plein écran
        self.root.attributes('-fullscreen', True)
        self.root.bind("<Escape>", lambda e: self.root.destroy())
        
        # --- Contrôles ---
        self.control_frame = tk.Frame(root, bg='#333333', padx=10, pady=5)
        self.control_frame.pack(side=tk.TOP, fill=tk.X)
        
        tk.Label(self.control_frame, text="CLIC GAUCHE: Casser un Rond ou un Tunnel  |  ÉCHAP: Quitter", 
                 bg='#333333', fg='#FFCC00', font=("Arial", 12, "bold")).pack(side=tk.RIGHT, padx=20)
        
        self.cols_var = tk.IntVar(value=15)
        self.rows_var = tk.IntVar(value=10)
        self.ants_var = tk.IntVar(value=60)
        
        # Les sliders redémarrent le graphe complètement
        self.scale_cols = tk.Scale(self.control_frame, variable=self.cols_var, from_=3, to=50, 
                                   orient=tk.HORIZONTAL, label="Largeur", bg='#333333', fg='white', 
                                   highlightthickness=0, command=self.schedule_reset)
        self.scale_cols.pack(side=tk.LEFT, padx=10)
        
        self.scale_rows = tk.Scale(self.control_frame, variable=self.rows_var, from_=3, to=30, 
                                   orient=tk.HORIZONTAL, label="Hauteur", bg='#333333', fg='white', 
                                   highlightthickness=0, command=self.schedule_reset)
        self.scale_rows.pack(side=tk.LEFT, padx=10)

        self.scale_ants = tk.Scale(self.control_frame, variable=self.ants_var, from_=1, to=200, 
                                   orient=tk.HORIZONTAL, label="Fourmis", bg='#333333', fg='white', 
                                   highlightthickness=0, command=self.schedule_reset)
        self.scale_ants.pack(side=tk.LEFT, padx=10)
        
        # --- Canvas ---
        self.canvas = tk.Canvas(root, bg='#111111', highlightthickness=0, cursor="crosshair")
        self.canvas.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        
        # Interaction clic
        self.canvas.bind("<Button-1>", self.on_click)
        
        self.draw_timer = None
        self.nodes = set()
        self.edges = set()
        self.ants = []
        
        self.root.update_idletasks()
        self.reset_graph()
        self.animate()

    def schedule_reset(self, event=None):
        if self.draw_timer is not None:
            self.root.after_cancel(self.draw_timer)
        self.draw_timer = self.root.after(200, self.reset_graph)

    def make_edge(self, n1, n2):
        """Crée un tuple ordonné pour identifier un tunnel de façon unique"""
        return (min(n1, n2), max(n1, n2))

    def reset_graph(self):
        """Crée la grille de départ"""
        self.canvas.delete("all")
        self.ants.clear()
        
        self.cols = self.cols_var.get()
        self.rows = self.rows_var.get()
        num_ants = self.ants_var.get()
        
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width <= 1:
            canvas_width = 1920
            canvas_height = 1000
            
        self.cell_size = min(canvas_width / self.cols, canvas_height / self.rows)
        self.margin_x = (canvas_width - (self.cell_size * self.cols)) / 2
        self.margin_y = (canvas_height - (self.cell_size * self.rows)) / 2
        
        self.circle_radius = (self.cell_size * 0.5) / 2
        self.tunnel_width = max(2, self.cell_size * 0.25)
        self.ant_radius = max(3, self.cell_size * 0.15)
        
        # 1. Générer tous les nœuds
        self.nodes = {(c, r) for c in range(self.cols) for r in range(self.rows)}
        
        # 2. Générer tous les tunnels (arêtes)
        self.edges = set()
        for r in range(self.rows):
            for c in range(self.cols):
                if c < self.cols - 1:
                    self.edges.add(self.make_edge((c, r), (c + 1, r)))
                if r < self.rows - 1:
                    self.edges.add(self.make_edge((c, r), (c, r + 1)))

        # 3. Placer les fourmis
        for _ in range(num_ants):
            self.spawn_ant()
            
        self.draw_graph()

    def get_coords(self, node):
        """Convertit (col, row) en (x, y) pixels"""
        cx = self.margin_x + node[0] * self.cell_size + self.cell_size / 2
        cy = self.margin_y + node[1] * self.cell_size + self.cell_size / 2
        return cx, cy

    def draw_graph(self):
        """Dessine uniquement l'arrière plan (Tunnels et Nœuds)"""
        self.canvas.delete("graph")
        
        # Dessiner les tunnels
        for e in self.edges:
            x1, y1 = self.get_coords(e[0])
            x2, y2 = self.get_coords(e[1])
            self.canvas.create_line(x1, y1, x2, y2, fill='#444455', width=self.tunnel_width, 
                                    capstyle=tk.ROUND, tags="graph")

        # Dessiner les nœuds
        for n in self.nodes:
            cx, cy = self.get_coords(n)
            self.canvas.create_oval(cx - self.circle_radius, cy - self.circle_radius, 
                                    cx + self.circle_radius, cy + self.circle_radius, 
                                    fill='#E0E0E0', outline='#222222', width=2, tags="graph")
            
        # S'assurer que les fourmis restent au premier plan
        self.canvas.tag_raise("ant")

    # --- LOGIQUE DE DESTRUCTION ---

    def on_click(self, event):
        px, py = event.x, event.y
        
        # 1. Vérifier si on a cliqué sur un rond
        for n in list(self.nodes):
            cx, cy = self.get_coords(n)
            dist = ((px - cx)**2 + (py - cy)**2)**0.5
            if dist <= self.circle_radius * 1.5:  # Légère tolérance de clic
                self.remove_node(n)
                self.draw_graph()
                return # On a détruit un rond, on s'arrête là

        # 2. Si aucun rond touché, vérifier si on a cliqué sur un tunnel
        for e in list(self.edges):
            x1, y1 = self.get_coords(e[0])
            x2, y2 = self.get_coords(e[1])
            dist = self.dist_to_segment(px, py, x1, y1, x2, y2)
            if dist <= self.tunnel_width * 1.5:
                self.edges.remove(e)
                self.draw_graph()
                return

    def remove_node(self, node):
        """Logique mathématique pour créer le grand pont quand on casse un rond"""
        # Trouver avec qui ce rond était connecté
        neighbors = []
        for e in self.edges:
            if e[0] == node: neighbors.append(e[1])
            elif e[1] == node: neighbors.append(e[0])
            
        new_bridges = []
        # Chercher des paires de voisins qui sont "alignés"
        for a, b in itertools.combinations(neighbors, 2):
            dx_a, dy_a = node[0] - a[0], node[1] - a[1]
            dx_b, dy_b = b[0] - node[0], b[1] - node[1]
            
            # Produit vectoriel (0 = ils sont sur la même ligne)
            cross_product = dx_a * dy_b - dy_a * dx_b
            # Produit scalaire (>0 = ils pointent dans la même direction / pas un demi-tour)
            dot_product = dx_a * dx_b + dy_a * dy_b
            
            if cross_product == 0 and dot_product > 0:
                # Ils sont parfaitement alignés de part et d'autre du trou ! On crée un pont.
                new_bridges.append(self.make_edge(a, b))
                
        # Nettoyer l'ancien rond et ses tunnels coupés
        self.edges = {e for e in self.edges if node not in e}
        if node in self.nodes:
            self.nodes.remove(node)
            
        # Ajouter les nouveaux grands ponts
        for bridge in new_bridges:
            self.edges.add(bridge)

    def dist_to_segment(self, px, py, x1, y1, x2, y2):
        """Mathématiques pour calculer la distance entre la souris et un segment de tunnel"""
        dx = x2 - x1
        dy = y2 - y1
        l2 = dx*dx + dy*dy
        if l2 == 0: return ((px - x1)**2 + (py - y1)**2)**0.5
        t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / l2))
        proj_x = x1 + t * dx
        proj_y = y1 + t * dy
        return ((px - proj_x)**2 + (py - proj_y)**2)**0.5

    # --- LOGIQUE DES FOURMIS ---

    def spawn_ant(self, existing_item=None):
        if not self.nodes:
            return None # Plus aucun rond sur l'écran
            
        start_node = random.choice(list(self.nodes))
        cx, cy = self.get_coords(start_node)
        
        if existing_item is None:
            item_id = self.canvas.create_oval(cx - self.ant_radius, cy - self.ant_radius, 
                                              cx + self.ant_radius, cy + self.ant_radius, 
                                              fill='#FF3366', outline='white', tags="ant")
            ant = {'item': item_id}
            self.ants.append(ant)
        else:
            ant = existing_item
            
        ant.update({
            'source': start_node,
            'target': start_node,
            'prev': start_node,
            'progress': 1.0,
            'speed': random.uniform(0.02, 0.06)
        })
        return ant

    def get_neighbors(self, node):
        neighbors = []
        for e in self.edges:
            if e[0] == node: neighbors.append(e[1])
            elif e[1] == node: neighbors.append(e[0])
        return neighbors

    def animate(self):
        for ant in self.ants:
            # Vérifier que le chemin où la fourmi se trouve existe toujours (sinon elle tombe dans le vide)
            if ant['progress'] < 1.0:
                current_edge = self.make_edge(ant['source'], ant['target'])
                if current_edge not in self.edges or ant['source'] not in self.nodes or ant['target'] not in self.nodes:
                    self.spawn_ant(ant) # Le chemin a été détruit par le joueur, téléportation !
                    continue

            # Arrivée à un rond
            if ant['progress'] >= 1.0:
                if ant['target'] not in self.nodes:
                    self.spawn_ant(ant)
                    continue
                    
                ant['source'] = ant['target']
                ant['progress'] = 0.0
                
                # Chercher où aller ensuite
                neighbors = self.get_neighbors(ant['source'])
                if not neighbors:
                    # Nœud isolé, on ne bouge plus ou on patiente
                    ant['target'] = ant['source']
                else:
                    # On évite de faire demi-tour si possible
                    valid_neighbors = [n for n in neighbors if n != ant['prev']]
                    if not valid_neighbors: 
                        valid_neighbors = neighbors # Cul de sac, obligé de faire demi-tour
                        
                    ant['target'] = random.choice(valid_neighbors)
                    ant['prev'] = ant['source']

            # Déplacement physique sur l'écran
            if ant['source'] != ant['target']:
                ant['progress'] += ant['speed']
                if ant['progress'] > 1.0: ant['progress'] = 1.0
                
                cx_start, cy_start = self.get_coords(ant['source'])
                cx_target, cy_target = self.get_coords(ant['target'])
                
                current_x = cx_start + (cx_target - cx_start) * ant['progress']
                current_y = cy_start + (cy_target - cy_start) * ant['progress']
                
                self.canvas.coords(ant['item'], 
                                   current_x - self.ant_radius, current_y - self.ant_radius,
                                   current_x + self.ant_radius, current_y + self.ant_radius)

        self.root.after(30, self.animate)

if __name__ == "__main__":
    root = tk.Tk()
    app = DestructibleNetwork(root)
    root.mainloop()