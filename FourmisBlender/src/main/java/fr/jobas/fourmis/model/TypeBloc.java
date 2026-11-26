package fr.jobas.fourmis.model;

/**
 * Les blocs posables sur l'étage 1. Une case sans bloc est un trou : infranchissable.
 * Le nom de la constante est envoyé tel quel à Blender.
 */
public enum TypeBloc {
  CHEMIN("Chemin", true, "#E8C27A"),
  SPAWN("Spawn (nid)", true, "#B5763A"),
  CAILLOU("Caillou", false, "#9AA0A8"),
  HERBE("Herbe", false, "#6CC24A"),
  FLEUR("Fleur", false, "#F28DC1"),
  FLAQUE("Flaque d'eau", false, "#4FB3F0"),
  SOUCHE("Souche", false, "#8A5A34");

  private final String libelle;
  private final boolean praticable;
  private final String couleur;

  TypeBloc(String libelle, boolean praticable, String couleur) {
    this.libelle = libelle;
    this.praticable = praticable;
    this.couleur = couleur;
  }

  public String getLibelle() {
    return libelle;
  }

  /** true si une fourmi peut marcher sur ce bloc. */
  public boolean estPraticable() {
    return praticable;
  }

  /** Couleur principale (hexadécimal) pour l'éditeur 2D. */
  public String getCouleur() {
    return couleur;
  }
}
