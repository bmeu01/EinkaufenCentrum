package fr.jobas.ui;

import fr.jobas.model.Arete;
import fr.jobas.model.Graph;
import fr.jobas.model.Noeud;
import java.util.HashMap;
import java.util.Map;
import javafx.geometry.Insets;
import javafx.scene.control.Button;
import javafx.scene.control.Label;
import javafx.scene.layout.BorderPane;
import javafx.scene.layout.HBox;
import javafx.scene.layout.Pane;
import javafx.scene.paint.Color;
import javafx.scene.shape.Circle;
import javafx.scene.shape.Line;

public class GrapheView extends BorderPane {

  private static final int MODE_AUCUN = 0;
  private static final int MODE_NOEUD = 1;
  private static final int MODE_ARETE = 2;

  private final Graph graph;
  private final Pane zoneDessin = new Pane();
  private final Label texteInfo = new Label("Choisis une action en haut");

  // Associe chaque Noeud du modèle à son Cercle affiché à l'écran
  private final Map<Noeud, Circle> cerclesParNoeud = new HashMap<>();

  private final Button btnNoeud = new Button("Ajouter Noeud");
  private final Button btnArete = new Button("Ajouter Arête");
  private final Button btnStart = new Button("Lancer Simulation");

  private int modeActuel = MODE_AUCUN;
  private Noeud premierNoeud = null;

  public GrapheView(Graph graph) {
    this.graph = graph;
    construireFenetre();
    configurerBoutons();
    configurerClicTerrain();
  }

  private void construireFenetre() {
    HBox barreHaut = new HBox(10);
    barreHaut.setPadding(new Insets(10));
    barreHaut.getChildren().addAll(btnNoeud, btnArete, btnStart, texteInfo);

    zoneDessin.setStyle("-fx-background-color: #222222;");

    this.setTop(barreHaut);
    this.setCenter(zoneDessin);
  }

  private void configurerBoutons() {
    btnNoeud.setOnAction(
        event -> {
          modeActuel = MODE_NOEUD;
          annulerSelectionArete();
          texteInfo.setText("Clique dans la zone noire pour poser un noeud");
        });

    btnArete.setOnAction(
        event -> {
          modeActuel = MODE_ARETE;
          annulerSelectionArete();
          texteInfo.setText("Clique sur un premier noeud");
        });

    btnStart.setOnAction(
        event -> {
          modeActuel = MODE_AUCUN;
          annulerSelectionArete();
          btnNoeud.setDisable(true);
          btnArete.setDisable(true);
          btnStart.setDisable(true);
          texteInfo.setText("Simulation en cours...");
        });
  }

  private void configurerClicTerrain() {
    zoneDessin.setOnMouseClicked(
        event -> {
          if (modeActuel == MODE_NOEUD) {
            creerEtAfficherNoeud(event.getX(), event.getY());
          }
        });
  }

  private void creerEtAfficherNoeud(double clicX, double clicY) {
    // 1. Création purement topologique dans le modèle (aucune coordonnée)
    Noeud nouveauNoeud = new Noeud();
    graph.ajouterNoeud(nouveauNoeud);

    // 2. Création visuelle à l'endroit du clic
    Circle cercle = new Circle(clicX, clicY, 15, Color.CORNFLOWERBLUE);
    cercle.setStroke(Color.WHITE);
    cercle.setStrokeWidth(2);

    // On enregistre le lien entre le noeud et son cercle
    cerclesParNoeud.put(nouveauNoeud, cercle);

    cercle.setOnMouseClicked(
        event -> {
          event.consume();
          if (modeActuel == MODE_ARETE) {
            clicSurNoeudPourArete(nouveauNoeud);
          }
        });

    zoneDessin.getChildren().add(cercle);
  }

  private void clicSurNoeudPourArete(Noeud noeudClique) {
    if (premierNoeud == null) {
      premierNoeud = noeudClique;
      cerclesParNoeud.get(premierNoeud).setStroke(Color.ORANGE);
      texteInfo.setText("Clique sur le deuxième noeud");
      return;
    }

    if (premierNoeud != noeudClique) {
      // 1. Ajout de l'arête dans le modèle
      Arete nouvelleArete = new Arete(premierNoeud, noeudClique);
      graph.ajouterArete(nouvelleArete);

      // 2. Récupération des cercles à l'écran pour tracer le trait entre eux
      Circle cercleDepart = cerclesParNoeud.get(premierNoeud);
      Circle cercleArrivee = cerclesParNoeud.get(noeudClique);

      Line trait =
          new Line(
              cercleDepart.getCenterX(), cercleDepart.getCenterY(),
              cercleArrivee.getCenterX(), cercleArrivee.getCenterY());
      trait.setStroke(Color.LIGHTGRAY);
      trait.setStrokeWidth(2);

      zoneDessin.getChildren().add(0, trait);

      annulerSelectionArete();
      texteInfo.setText("Arête ajoutée ! Clique sur un noeud pour continuer");
    }
  }

  private void annulerSelectionArete() {
    if (premierNoeud != null) {
      cerclesParNoeud.get(premierNoeud).setStroke(Color.WHITE);
    }
    premierNoeud = null;
  }
}
