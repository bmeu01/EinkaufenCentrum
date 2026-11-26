package fr.jobas.fourmis.simulation;

import fr.jobas.fourmis.model.Position;

/** Une fourmi : sa case actuelle, la précédente et sa direction (dx, dy). */
public class Fourmi {
  private final int id;
  private Position position;
  private Position precedente;
  private int dx;
  private int dy;

  public Fourmi(int id, Position depart) {
    this.id = id;
    this.position = depart;
  }

  void deplacerVers(Position cible) {
    dx = cible.getX() - position.getX();
    dy = cible.getY() - position.getY();
    precedente = position;
    position = cible;
  }

  public int getId() {
    return id;
  }

  public Position getPosition() {
    return position;
  }

  public Position getPrecedente() {
    return precedente;
  }

  public int getDx() {
    return dx;
  }

  public int getDy() {
    return dy;
  }
}
