package fr.jobas;

import javafx.application.Application;
import javafx.scene.Scene;
import javafx.scene.control.Label;
import javafx.scene.layout.StackPane;
import javafx.stage.Stage;

/** JavaFX App */
public class App extends Application {

  @Override
  public void init() {
    // Read the files and create the objects
  }

  // Start the UI
  @Override
  public void start(Stage stage) {
    var javaVersion = SystemInfo.javaVersion();
    var javafxVersion = SystemInfo.javafxVersion();

    var label =
        new Label("Hello, JavaFX " + javafxVersion + ", running on Java " + javaVersion + ".");
    var scene = new Scene(new StackPane(label), 640, 480);
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
  // Creer l'UI d'acceuille (bouton jouer et boutton paramètre)
  // Bouton jouer
  // Lire un json qui sauvegarde l'ancien terrain ou un terrain par défaut (graphe topologique)
  // 2. Creer l'UI pour placer les choses (temps de placement), nombre de fourmis, taille du
  // terrain. Sauvegarde du terrain et chargement du terrain.
  // 3. Boutton lancer! (Passage en mode simulation)
  // Spawn du nombre de fourmis par equipe
  // Fourmis qui suit les féromones (X %) ou bien qui déville (X %) en fonction du rôle
  // 2 types de phéromones 1. vers maison (quand ne porte pas de bouffe) 2. vers bouffe (quand
  // rentre à la maison avec bouffe) 3. il n'y a plus rien à manger/transporter
  // Pheromones : évaporation
  // quand une fourmis bouge elle perd de la nourriture si sont compteur arrive à 0 elle meurt, elle
  // peut manger si elle a de la bouffe ou bien elle touche le nid et il y a de la bouffe. Si
  // il y a assez de bouffe dans la colonie création de nouvelle

  // Si croise enemy feromone alerte et les guerriers les suives
  // Attention chaque fourmis à une colision contr mur et nid mais SURTOUT pas entre fourmis
}
