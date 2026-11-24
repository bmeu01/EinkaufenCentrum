package fr.jobas;

import fr.jobas.model.Graph;
import fr.jobas.ui.GrapheView;
import javafx.application.Application;
import javafx.scene.Scene;
import javafx.stage.Stage;

/** JavaFX App */
public class App extends Application {
  Graph graph;

  @Override
  public void init() {
    // Read the files and create the objects
    // TODO ajout des noeuds et des aretes dans graph
    graph = new Graph();
  }

  // Start the UI
  @Override
  public void start(Stage stage) {
    GrapheView vue = new GrapheView(this.graph);
    Scene scene = new Scene(vue, 900, 600);

    stage.setTitle("Simulation Fourmilière");
    stage.setScene(scene);
    stage.show();
  }

  @Override
  public void stop() {
    // Save the map and kill the sim
  }

  public static void main(String[] args) {
    launch();
    // initialize_map()
  }
  // TODO
  // 1. Édition du graphe et des entités
  // - Permettre de choisir le type de noeud lors du placement (Nid équipe 1, Nid équipe 2, Nourriture, Salle vide)
  // - Ajouter les fourmis (bouton ou champ pour définir le nombre par équipe, spawn sur les nids et affichage visuel)

  // 2. Sauvegarde et chargement (JSON)
  // - Ajouter une dépendance JSON (Gson ou Jackson) dans pom.xml
  // - Sauvegarder le graphe (noeuds, types, arêtes) dans App.stop() ou via un bouton
  // - Charger un terrain par défaut ou sauvegardé dans App.init()

  // 3. Moteur de simulation (après clic sur "Lancer Simulation")
  // - Créer la boucle de simulation (AnimationTimer ou Timeline)
  // - Déplacer les fourmis d'un noeud à l'autre via les arêtes
  // - Implémenter le choix de chemin : suivre les phéromones (X %) ou explorer aléatoirement (Y %) selon le rôle
  // - Gérer les 3 phéromones par équipe : 1. vers nid, 2. vers nourriture, 3. plus de nourriture
  // - Ajouter l'évaporation progressive des phéromones à chaque tour
  // - Gérer la faim : perte d'énergie à chaque déplacement, mort à 0, ravitaillement si la fourmi porte de la nourriture ou atteint son nid
  // - Créer une nouvelle fourmi si le stock de nourriture du nid dépasse un seuil
  // - Gérer l'alerte : si une phéromone ennemie est croisée, alerter et attirer les guerriers
  // - Respecter la capacité max et l'accessibilité des noeuds/arêtes (sans blocage bloquant entre fourmis)

  // 4. Finitions UI (à faire en dernier)
  // - Créer l'écran d'accueil (bouton Jouer, bouton Paramètres pour régler les taux et le nombre de fourmis)}
