package fr.jobas.fourmis.model;

/** Une case de la grille (x = colonne, y = ligne). Immuable : sert de clé dans la HashMap. */
public final class Position {
  private final int x;
  private final int y;

  public Position(int x, int y) {
    this.x = x;
    this.y = y;
  }

  public int getX() {
    return x;
  }

  public int getY() {
    return y;
  }

  public Position decaler(int dx, int dy) {
    return new Position(x + dx, y + dy);
  }

  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (!(o instanceof Position)) {
      return false;
    }
    Position p = (Position) o;
    return x == p.x && y == p.y;
  }

  @Override
  public int hashCode() {
    return 31 * x + y;
  }

  @Override
  public String toString() {
    return "(" + x + ", " + y + ")";
  }
}
