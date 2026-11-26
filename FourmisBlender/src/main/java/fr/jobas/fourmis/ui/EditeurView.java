package fr.jobas.fourmis.ui;

import fr.jobas.fourmis.blender.BlenderClient;
import fr.jobas.fourmis.blender.Protocole;
import fr.jobas.fourmis.model.Carte;
import fr.jobas.fourmis.model.CartesExemple;
import fr.jobas.fourmis.model.Position;
import fr.jobas.fourmis.model.TypeBloc;
import fr.jobas.fourmis.simulation.Fourmi;
import fr.jobas.fourmis.simulation.Simulation;
import javafx.animation.Animation;
import javafx.animation.KeyFrame;
import javafx.animation.Timeline;
import javafx.application.Platform;
import javafx.geometry.Insets;
import javafx.geometry.Pos;
import javafx.scene.canvas.Canvas;
import javafx.scene.canvas.GraphicsContext;
import javafx.scene.control.Button;
import javafx.scene.control.Label;
import javafx.scene.control.Separator;
import javafx.scene.control.Slider;
import javafx.scene.control.Spinner;
import javafx.scene.control.ToggleButton;
import javafx.scene.control.ToggleGroup;
import javafx.scene.input.MouseButton;
import javafx.scene.input.MouseEvent;
import javafx.scene.layout.BorderPane;
import javafx.scene.layout.VBox;
import javafx.scene.paint.Color;
import javafx.scene.shape.Rectangle;
import javafx.scene.text.Font;
import javafx.scene.text.FontWeight;
import javafx.util.Duration;

/**
 * Fenêtre principale. À gauche la palette de blocs, au centre la grille 2D, à droite les
 * réglages. Clic gauche (ou glisser) : poser le bloc choisi. Clic droit : supprimer.
 */
public class EditeurView extends BorderPane {

  private static final int CELLULE = 30;
  private static final int TICK_REFERENCE_MS = 100;
  private static final Color FOND_VIDE = Color.web("#5A4432");
  private static final Color GRILLE = Color.web("#00000033");

  private final Carte carte;
  private final Canvas canvas;
  private final ToggleGroup groupeOutils = new ToggleGroup();
  private final Label statut = new Label();
  private final Spinner<Integer> nbFourmis = new Spinner<>(1, 80, 15);
  private final Slider vitesse = new Slider(120, 1000, 350);
  private final Slider inertie = new Slider(0, 0.9, 0.45);
  private final Button btnLancer = new Button("▶  Lancer la simulation");
  private final Button btnArreter = new Button("■  Arrêter");
  private final Button btnVider = new Button("Tout en chemin");
  private final Button btnExemple = new Button("Carte d'exemple");
  private final VBox palette = new VBox(6);
  private final BlenderClient blender = new BlenderClient();

  private TypeBloc outil = TypeBloc.CHEMIN; // null = gomme
  private Simulation simulation;
  private Timeline boucle;
  private Position derniereCase;

  public EditeurView(Carte carte) {
    this.carte = carte;
    this.canvas = new Canvas(carte.getTaille() * CELLULE, carte.getTaille() * CELLULE);
    construirePalette();
    construireReglages();
    configurerSouris();

    BorderPane.setMargin(canvas, new Insets(12));
    setCenter(canvas);
    statut.setPadding(new Insets(6, 12, 10, 12));
    statut.setWrapText(true);
    setBottom(statut);
    setStyle("-fx-background-color: #F4EDE1;");

    afficher("Tout est en chemin au départ : posez des obstacles, un Spawn, puis lancez la simulation.");
    dessiner();
  }

  // ------------------------------------------------------------------ construction de l'UI

  private void construirePalette() {
    Label titre = new Label("Blocs");
    titre.setFont(Font.font(null, FontWeight.BOLD, 14));
    palette.getChildren().add(titre);
    for (TypeBloc t : TypeBloc.values()) {
      palette.getChildren().add(boutonOutil(t.getLibelle(), Color.web(t.getCouleur()), t));
    }
    palette.getChildren().add(boutonOutil("Gomme (chemin)", Color.web(TypeBloc.CHEMIN.getCouleur()), null));
    Label aide =
        new Label("Clic gauche : poser\nClic droit : remettre\ndu chemin\n\nPraticables :\nChemin, Spawn");
    aide.setStyle("-fx-text-fill: #6b5a48;");
    palette.getChildren().addAll(new Separator(), aide);
    palette.setPadding(new Insets(12));
    palette.setPrefWidth(150);
    groupeOutils.getToggles().get(0).setSelected(true);
    setLeft(palette);
  }

  private ToggleButton boutonOutil(String libelle, Color couleur, TypeBloc type) {
    Rectangle pastille = new Rectangle(14, 14, couleur);
    pastille.setArcWidth(5);
    pastille.setArcHeight(5);
    pastille.setStroke(Color.web("#00000055"));
    ToggleButton b = new ToggleButton(libelle, pastille);
    b.setToggleGroup(groupeOutils);
    b.setMaxWidth(Double.MAX_VALUE);
    b.setAlignment(Pos.CENTER_LEFT);
    b.setOnAction(
        e -> {
          if (!b.isSelected()) {
            b.setSelected(true); // toujours un outil actif
          }
          outil = type;
        });
    return b;
  }

  private void construireReglages() {
    nbFourmis.setEditable(true);
    nbFourmis.setPrefWidth(90);
    vitesse.setShowTickLabels(true);
    vitesse.setMajorTickUnit(440);
    inertie.setShowTickLabels(true);
    inertie.setMajorTickUnit(0.45);

    vitesse.valueProperty().addListener((obs, a, b) -> appliquerVitesse());

    btnLancer.setMaxWidth(Double.MAX_VALUE);
    btnArreter.setMaxWidth(Double.MAX_VALUE);
    btnVider.setMaxWidth(Double.MAX_VALUE);
    btnExemple.setMaxWidth(Double.MAX_VALUE);
    btnLancer.setStyle("-fx-font-weight: bold; -fx-base: #8FD16A;");
    btnArreter.setDisable(true);

    btnLancer.setOnAction(e -> lancer());
    btnArreter.setOnAction(e -> arreter());
    btnVider.setOnAction(
        e -> {
          carte.vider();
          dessiner();
          afficher("Carte remise à zéro : tout est en chemin.");
        });
    btnExemple.setOnAction(
        e -> {
          CartesExemple.remplirJardin(carte);
          dessiner();
          afficher("Carte d'exemple chargée. Lancez la simulation !");
        });

    VBox droite =
        new VBox(
            8,
            titre("Simulation"),
            new Label("Nombre de fourmis"),
            nbFourmis,
            new Label("Durée d'un pas (ms)"),
            vitesse,
            new Label("Envie d'aller tout droit"),
            inertie,
            new Separator(),
            btnLancer,
            btnArreter,
            new Separator(),
            btnExemple,
            btnVider,
            new Separator(),
            new Label("Blender : 127.0.0.1:" + BlenderClient.PORT));
    droite.setPadding(new Insets(12));
    droite.setPrefWidth(200);
    setRight(droite);
  }

  private static Label titre(String texte) {
    Label l = new Label(texte);
    l.setFont(Font.font(null, FontWeight.BOLD, 14));
    return l;
  }

  // ------------------------------------------------------------------ édition à la souris

  private void configurerSouris() {
    canvas.setOnMousePressed(
        e -> {
          derniereCase = null;
          editer(e);
        });
    canvas.setOnMouseDragged(this::editer);
  }

  private void editer(MouseEvent e) {
    if (simulation != null) {
      return; // pas d'édition pendant la simulation
    }
    Position p = new Position((int) (e.getX() / CELLULE), (int) (e.getY() / CELLULE));
    if (!carte.dansLaGrille(p) || p.equals(derniereCase)) {
      return;
    }
    derniereCase = p;
    if (e.getButton() == MouseButton.SECONDARY || outil == null) {
      carte.supprimer(p);
    } else {
      String refus = carte.placer(p, outil);
      if (refus != null) {
        afficher(refus);
      }
    }
    dessiner();
  }

  // ------------------------------------------------------------------ simulation

  private void lancer() {
    if (carte.getSpawn() == null) {
      afficher("Placez d'abord un bloc Spawn : c'est de là que partent les fourmis.");
      return;
    }
    int accessibles = carte.casesAccessiblesDepuisSpawn();
    simulation =
        new Simulation(carte, nbFourmis.getValue(), inertie.getValue(), System.nanoTime());
    setEdition(false);
    afficher("Connexion à Blender…");

    blender
        .connecter()
        .thenAccept(
            ok ->
                Platform.runLater(
                    () -> {
                      if (simulation == null) {
                        return; // arrêtée entre-temps
                      }
                      if (ok) {
                        blender.envoyer(Protocole.carte(carte, dureePasMs()));
                        afficher("Simulation en cours, affichée dans Blender.");
                      } else {
                        afficher(
                            "Blender non joignable : simulation affichée en 2D seulement."
                                + " Lancez fourmis_blender.py dans Blender puis relancez.");
                      }
                      if (accessibles <= 1) {
                        afficher(
                            statut.getText()
                                + "  Attention : aucun chemin ne touche le spawn, les"
                                + " fourmis resteront sur place.");
                      }
                      demarrerBoucle();
                    }));
  }

  private void demarrerBoucle() {
    boucle =
        new Timeline(new KeyFrame(Duration.millis(TICK_REFERENCE_MS), e -> pasDeSimulation()));
    boucle.setCycleCount(Animation.INDEFINITE);
    appliquerVitesse();
    boucle.play();
  }

  private void pasDeSimulation() {
    if (simulation == null) {
      return;
    }
    simulation.tick();
    blender.envoyer(
        Protocole.fourmis(simulation.getTick(), dureePasMs(), simulation.getFourmis()));
    dessiner();
  }

  private void appliquerVitesse() {
    if (boucle != null) {
      boucle.setRate((double) TICK_REFERENCE_MS / dureePasMs());
    }
  }

  private int dureePasMs() {
    return (int) Math.round(vitesse.getValue());
  }

  private void arreter() {
    if (boucle != null) {
      boucle.stop();
      boucle = null;
    }
    simulation = null;
    blender.envoyer(Protocole.stop());
    blender.deconnecter();
    setEdition(true);
    dessiner();
    afficher("Simulation arrêtée. Vous pouvez modifier la carte.");
  }

  private void setEdition(boolean active) {
    palette.setDisable(!active);
    btnLancer.setDisable(!active);
    btnVider.setDisable(!active);
    btnExemple.setDisable(!active);
    nbFourmis.setDisable(!active);
    inertie.setDisable(!active);
    btnArreter.setDisable(active);
  }

  /** À appeler quand la fenêtre se ferme. */
  public void fermer() {
    if (boucle != null) {
      boucle.stop();
    }
    if (simulation != null) {
      blender.envoyer(Protocole.stop());
    }
    blender.close();
  }

  private void afficher(String message) {
    statut.setText(message);
  }

  // ------------------------------------------------------------------ dessin 2D

  private void dessiner() {
    GraphicsContext g = canvas.getGraphicsContext2D();
    int n = carte.getTaille();
    g.setFill(FOND_VIDE);
    g.fillRect(0, 0, canvas.getWidth(), canvas.getHeight());

    for (int y = 0; y < n; y++) {
      for (int x = 0; x < n; x++) {
        TypeBloc t = carte.getBloc(new Position(x, y));
        if (t != null) {
          dessinerBloc(g, t, x * CELLULE, y * CELLULE);
        }
      }
    }

    g.setStroke(GRILLE);
    g.setLineWidth(1);
    for (int i = 0; i <= n; i++) {
      g.strokeLine(i * CELLULE + 0.5, 0, i * CELLULE + 0.5, n * CELLULE);
      g.strokeLine(0, i * CELLULE + 0.5, n * CELLULE, i * CELLULE + 0.5);
    }

    if (simulation != null) {
      for (Fourmi f : simulation.getFourmis()) {
        dessinerFourmi(g, f);
      }
    }
  }

  private void dessinerBloc(GraphicsContext g, TypeBloc t, double px, double py) {
    double c = CELLULE;
    double m = c / 2;
    switch (t) {
      case CHEMIN:
        g.setFill(Color.web(t.getCouleur()));
        g.fillRect(px, py, c, c);
        g.setFill(Color.web("#D4AA5E"));
        g.fillOval(px + 6, py + 8, 3, 3);
        g.fillOval(px + 19, py + 18, 3, 3);
        break;
      case SPAWN:
        g.setFill(Color.web(TypeBloc.CHEMIN.getCouleur()));
        g.fillRect(px, py, c, c);
        g.setFill(Color.web(t.getCouleur()));
        g.fillOval(px + 3, py + 3, c - 6, c - 6);
        g.setFill(Color.web("#2B1A10"));
        g.fillOval(px + m - 5, py + m - 5, 10, 10);
        break;
      case CAILLOU:
        g.setFill(Color.web("#C9B48A"));
        g.fillRect(px, py, c, c);
        g.setFill(Color.web(t.getCouleur()));
        g.fillOval(px + 4, py + 6, 18, 15);
        g.setFill(Color.web("#7D838B"));
        g.fillOval(px + 16, py + 15, 11, 10);
        break;
      case HERBE:
        g.setFill(Color.web(t.getCouleur()));
        g.fillRect(px, py, c, c);
        g.setStroke(Color.web("#3E8E2A"));
        g.setLineWidth(2);
        for (int i = 0; i < 4; i++) {
          double bx = px + 6 + i * 6;
          g.strokeLine(bx, py + c - 6, bx + (i % 2 == 0 ? -2 : 2), py + 8 + (i % 2) * 4);
        }
        break;
      case FLEUR:
        g.setFill(Color.web(TypeBloc.HERBE.getCouleur()));
        g.fillRect(px, py, c, c);
        g.setFill(Color.web(t.getCouleur()));
        for (int i = 0; i < 5; i++) {
          double a = i * 2 * Math.PI / 5;
          g.fillOval(px + m - 4 + 6 * Math.cos(a), py + m - 4 + 6 * Math.sin(a), 8, 8);
        }
        g.setFill(Color.web("#FFD43B"));
        g.fillOval(px + m - 3, py + m - 3, 6, 6);
        break;
      case FLAQUE:
        g.setFill(Color.web("#C9B48A"));
        g.fillRect(px, py, c, c);
        g.setFill(Color.web(t.getCouleur()));
        g.fillOval(px + 3, py + 5, c - 6, c - 10);
        g.setFill(Color.web("#FFFFFFAA"));
        g.fillOval(px + 8, py + 9, 7, 3);
        break;
      case SOUCHE:
        g.setFill(Color.web(TypeBloc.HERBE.getCouleur()));
        g.fillRect(px, py, c, c);
        g.setFill(Color.web(t.getCouleur()));
        g.fillOval(px + 4, py + 4, c - 8, c - 8);
        g.setStroke(Color.web("#D9A86C"));
        g.setLineWidth(1.5);
        g.strokeOval(px + 9, py + 9, c - 18, c - 18);
        break;
      default:
        g.setFill(Color.web(t.getCouleur()));
        g.fillRect(px, py, c, c);
    }
  }

  private void dessinerFourmi(GraphicsContext g, Fourmi f) {
    // petit décalage par fourmi pour qu'on les distingue sur une même case
    double ox = ((f.getId() * 37) % 9 - 4) * 1.2;
    double oy = ((f.getId() * 53) % 9 - 4) * 1.2;
    double cx = f.getPosition().getX() * CELLULE + CELLULE / 2.0 + ox;
    double cy = f.getPosition().getY() * CELLULE + CELLULE / 2.0 + oy;
    boolean horizontale = f.getDx() != 0;
    double lx = horizontale ? 12 : 7;
    double ly = horizontale ? 7 : 12;
    g.setFill(Color.web("#8B2E1F"));
    g.fillOval(cx - lx / 2, cy - ly / 2, lx, ly);
    g.setStroke(Color.web("#1E0F08"));
    g.setLineWidth(1.2);
    g.strokeOval(cx - lx / 2, cy - ly / 2, lx, ly);
  }
}
