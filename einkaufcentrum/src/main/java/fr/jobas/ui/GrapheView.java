package fr.jobas.ui;

import fr.jobas.model.Arete;
import fr.jobas.model.GameState;
import fr.jobas.model.Graph;
import fr.jobas.model.Nid;
import fr.jobas.model.Noeud;
import fr.jobas.model.Nourriture;
import fr.jobas.model.TypeSalle;
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
  private final Map<Noeud, Nid> nidsParNoeud = new HashMap<>();
  private final Map<Noeud, Nourriture> nourrituresParNoeud = new HashMap<>();

  private final Button btnNoeud = new Button("Ajouter Noeud");
  private final Button btnArete = new Button("Ajouter Arête");
  private final Button btnNid = new Button("Ajouter Nid");
  private final Button btnNourriture = new Button("Ajouter Nourriture");
  private final Button btnStart = new Button("Lancer Simulation");

  private int modeActuel = MODE_AUCUN;
  private Noeud premierNoeud = null;

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
          actualiserEtatEtMessage("Clique sur un noeud de passage pour y placer un nid");
        });

    btnNourriture.setOnAction(
        event -> {
          modeActuel = MODE_NOURRITURE;
          annulerSelectionArete();
          actualiserEtatEtMessage("Clique sur un noeud de passage pour y placer de la nourriture");
        });

    btnStart.setOnAction(
        event -> {
          if (nidsParNoeud.isEmpty() || nourrituresParNoeud.isEmpty()) {
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
          if (modeActuel == MODE_NOEUD) {
            creerEtAfficherNoeud(event.getX(), event.getY());
          }
        });
  }

  private void creerEtAfficherNoeud(double clicX, double clicY) {
    Noeud nouveauNoeud = new Noeud();
    graph.ajouterNoeud(nouveauNoeud);

    Circle cercle = new Circle(clicX, clicY, 15, Color.CORNFLOWERBLUE);
    cercle.setStroke(Color.WHITE);
    cercle.setStrokeWidth(2);

    cerclesParNoeud.put(nouveauNoeud, cercle);

    cercle.setOnMouseClicked(
        event -> {
          event.consume();
          if (modeActuel == MODE_ARETE) {
            clicSurNoeudPourArete(nouveauNoeud);
          } else if (modeActuel == MODE_NID) {
            clicSurNoeudPourNid(nouveauNoeud);
          } else if (modeActuel == MODE_NOURRITURE) {
            clicSurNoeudPourNourriture(nouveauNoeud);
          }
        });

    zoneDessin.getChildren().add(cercle);
  }

  private void clicSurNoeudPourNid(Noeud noeudClique) {
    if (noeudClique.getTypeSalle() != TypeSalle.PASSAGE) {
      actualiserEtatEtMessage("Ce noeud est déjà occupé (" + noeudClique.getTypeSalle() + ")");
      return;
    }

    noeudClique.setTypeSalle(TypeSalle.NID);
    int numeroEquipe = nidsParNoeud.size() + 1;
    Nid nouveauNid = new Nid("Equipe " + numeroEquipe, noeudClique);
    nidsParNoeud.put(noeudClique, nouveauNid);

    Circle cercle = cerclesParNoeud.get(noeudClique);
    cercle.setFill(Color.CRIMSON);
    cercle.setStroke(Color.GOLD);
    cercle.setStrokeWidth(3);
    cercle.setRadius(18);

    actualiserEtatEtMessage("Nid ajouté (" + nouveauNid.getNomEquipe() + ")");
  }

  private void clicSurNoeudPourNourriture(Noeud noeudClique) {
    if (noeudClique.getTypeSalle() != TypeSalle.PASSAGE) {
      actualiserEtatEtMessage("Ce noeud est déjà occupé (" + noeudClique.getTypeSalle() + ")");
      return;
    }

    noeudClique.setTypeSalle(TypeSalle.NOURRITURE);
    Nourriture nouvelleNourriture = new Nourriture(noeudClique, 100);
    nourrituresParNoeud.put(noeudClique, nouvelleNourriture);

    Circle cercle = cerclesParNoeud.get(noeudClique);
    cercle.setFill(Color.LIMEGREEN);
    cercle.setStroke(Color.DARKGREEN);
    cercle.setStrokeWidth(3);
    cercle.setRadius(17);

    actualiserEtatEtMessage("Nourriture ajoutée");
  }

  private String getTexteManquant() {
    boolean manqueNid = nidsParNoeud.isEmpty();
    boolean manqueNourriture = nourrituresParNoeud.isEmpty();

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
    boolean pret = !nidsParNoeud.isEmpty() && !nourrituresParNoeud.isEmpty();
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
      switch (premierNoeud.getTypeSalle()) {
        case NID:
          couleurBordure = Color.GOLD;
          break;
        case NOURRITURE:
          couleurBordure = Color.DARKGREEN;
          break;
        default:
          couleurBordure = Color.WHITE;
          break;
      }
      cerclesParNoeud.get(premierNoeud).setStroke(couleurBordure);
    }
    premierNoeud = null;
  }
}
