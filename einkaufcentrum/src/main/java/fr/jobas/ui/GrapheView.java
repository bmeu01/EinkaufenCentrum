package fr.jobas.ui;

import fr.jobas.model.Arete;
import fr.jobas.model.GameState;
import fr.jobas.model.Graph;
import fr.jobas.model.Nid;
import fr.jobas.model.Noeud;
import fr.jobas.model.Nourriture;
import fr.jobas.simulation.MoteurSimulation;
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
  private static final int MODE_NID = 3;
  private static final int MODE_NOURRITURE = 4;

  private final GameState state;
  private final Graph graph;
  private final Pane zoneDessin = new Pane();
  private final Label texteInfo = new Label();

  private final Map<Noeud, Circle> cerclesParNoeud = new HashMap<>();

  private final Button btnNoeud = new Button("Ajouter Noeud");
  private final Button btnArete = new Button("Ajouter Arête");
  private final Button btnNid = new Button("Ajouter Nid");
  private final Button btnNourriture = new Button("Ajouter Nourriture");
  private final Button btnStart = new Button("Lancer Simulation");

  private int modeActuel = MODE_AUCUN;
  private Noeud premierNoeud = null;
  private int nbNids = 0;
  private int nbNourritures = 0;

  public GrapheView(Graph graph, GameState state) {
    this.graph = graph;
    this.state = state;
    construireFenetre();
    configurerBoutons();
    configurerClicTerrain();
  }

  private void construireFenetre() {
    HBox barreHaut = new HBox(10);
    barreHaut.setPadding(new Insets(10));
    barreHaut.getChildren().addAll(btnNoeud, btnArete, btnNid, btnNourriture, btnStart, texteInfo);

    zoneDessin.setStyle("-fx-background-color: #222222;");

    this.setTop(barreHaut);
    this.setCenter(zoneDessin);
    actualiserEtatEtMessage("Choisis une action en haut");
  }

  private void configurerBoutons() {
    btnNoeud.setOnAction(
        event -> {
          modeActuel = MODE_NOEUD;
          annulerSelectionArete();
          actualiserEtatEtMessage("Clique dans la zone noire pour poser un noeud");
        });

    btnArete.setOnAction(
        event -> {
          modeActuel = MODE_ARETE;
          annulerSelectionArete();
          actualiserEtatEtMessage("Clique sur un premier noeud");
        });

    btnNid.setOnAction(
        event -> {
          modeActuel = MODE_NID;
          annulerSelectionArete();
          actualiserEtatEtMessage("Clique dans la zone noire pour poser un nid");
        });

    btnNourriture.setOnAction(
        event -> {
          modeActuel = MODE_NOURRITURE;
          annulerSelectionArete();
          actualiserEtatEtMessage("Clique dans la zone noire pour poser de la nourriture");
        });

    btnStart.setOnAction(
        event -> {
          if (nbNids == 0 || nbNourritures == 0) {
            actualiserEtatEtMessage("Impossible de lancer");
            return;
          }
          modeActuel = MODE_AUCUN;
          annulerSelectionArete();
          btnNoeud.setDisable(true);
          btnArete.setDisable(true);
          btnNid.setDisable(true);
          btnNourriture.setDisable(true);
          btnStart.setDisable(true);
          texteInfo.setText("Simulation en cours...");
          new MoteurSimulation(graph, state);
        });
  }

  private void configurerClicTerrain() {
    zoneDessin.setOnMouseClicked(
        event -> {
          double x = event.getX();
          double y = event.getY();

          if (modeActuel == MODE_NOEUD) {
            Noeud noeud = new Noeud();
            ajouterSommetVisuel(noeud, x, y, 15, Color.CORNFLOWERBLUE, Color.WHITE, 2);
            actualiserEtatEtMessage("Noeud ajouté");
          } else if (modeActuel == MODE_NID) {
            nbNids++;
            Nid nid = new Nid("Equipe " + nbNids);
            ajouterSommetVisuel(nid, x, y, 18, Color.CRIMSON, Color.GOLD, 3);
            actualiserEtatEtMessage("Nid ajouté (" + nid.getNomEquipe() + ")");
          } else if (modeActuel == MODE_NOURRITURE) {
            nbNourritures++;
            Nourriture nourriture = new Nourriture(100);
            ajouterSommetVisuel(nourriture, x, y, 17, Color.LIMEGREEN, Color.DARKGREEN, 3);
            actualiserEtatEtMessage("Nourriture ajoutée");
          }
        });
  }

  private void ajouterSommetVisuel(
      Noeud sommet,
      double clicX,
      double clicY,
      double rayon,
      Color couleurFond,
      Color couleurBordure,
      double epaisseurBordure) {
    graph.ajouterNoeud(sommet);

    Circle cercle = new Circle(clicX, clicY, rayon, couleurFond);
    cercle.setStroke(couleurBordure);
    cercle.setStrokeWidth(epaisseurBordure);

    cerclesParNoeud.put(sommet, cercle);

    cercle.setOnMouseClicked(
        event -> {
          event.consume();
          if (modeActuel == MODE_ARETE) {
            clicSurNoeudPourArete(sommet);
          }
        });

    zoneDessin.getChildren().add(cercle);
  }

  private String getTexteManquant() {
    boolean manqueNid = nbNids == 0;
    boolean manqueNourriture = nbNourritures == 0;

    if (manqueNid && manqueNourriture) {
      return " (Manque : 1 nid et 1 nourriture)";
    } else if (manqueNid) {
      return " (Manque : 1 nid)";
    } else if (manqueNourriture) {
      return " (Manque : 1 nourriture)";
    }
    return " (Prêt à lancer !)";
  }

  private void actualiserEtatEtMessage(String actionEnCours) {
    boolean pret = nbNids > 0 && nbNourritures > 0;
    btnStart.setDisable(!pret);
    texteInfo.setText(actionEnCours + getTexteManquant());
  }

  private void clicSurNoeudPourArete(Noeud noeudClique) {
    if (premierNoeud == null) {
      premierNoeud = noeudClique;
      cerclesParNoeud.get(premierNoeud).setStroke(Color.ORANGE);
      actualiserEtatEtMessage("Clique sur le deuxième noeud");
      return;
    }

    if (premierNoeud != noeudClique) {
      Arete nouvelleArete = new Arete(premierNoeud, noeudClique);
      graph.ajouterArete(nouvelleArete);

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
      actualiserEtatEtMessage("Arête ajoutée ! Clique sur un noeud pour continuer");
    }
  }

  private void annulerSelectionArete() {
    if (premierNoeud != null) {
      Color couleurBordure;
      if (premierNoeud instanceof Nid) {
        couleurBordure = Color.GOLD;
      } else if (premierNoeud instanceof Nourriture) {
        couleurBordure = Color.DARKGREEN;
      } else {
        couleurBordure = Color.WHITE;
      }
      cerclesParNoeud.get(premierNoeud).setStroke(couleurBordure);
    }
    premierNoeud = null;
  }
}