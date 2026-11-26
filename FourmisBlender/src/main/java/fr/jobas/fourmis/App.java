package fr.jobas.fourmis;

import fr.jobas.fourmis.model.Carte;
import fr.jobas.fourmis.ui.EditeurView;
import javafx.application.Application;
import javafx.scene.Scene;
import javafx.stage.Stage;

/** Éditeur de carte 2D + simulation de fourmis, affichée en 3D dans Blender. */
public class App extends Application {

  public static final int TAILLE_CARTE = 20;

  private EditeurView editeur;

  @Override
  public void start(Stage stage) {
    editeur = new EditeurView(new Carte(TAILLE_CARTE));
    stage.setTitle("Fourmis — éditeur de terrain");
    stage.setScene(new Scene(editeur));
    stage.setResizable(false);
    stage.show();
  }

  @Override
  public void stop() {
    if (editeur != null) {
      editeur.fermer();
    }
  }

  public static void main(String[] args) {
    launch(args);
  }
}
