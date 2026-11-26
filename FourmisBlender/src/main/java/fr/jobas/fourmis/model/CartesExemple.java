package fr.jobas.fourmis.model;

/** Une carte 20x20 toute prête, pour tester vite : un jardin-labyrinthe. */
public final class CartesExemple {

  // . herbe  # chemin   S spawn   C caillou   H herbe   F fleur   E flaque   T souche
  private static final String[] JARDIN = {
    "HHFHHHCCHHHHTHHFFHHH",
    "H##################H",
    "F#HHFH#CCH#EEEHH#HHF",
    "H#H..H#C..#EE..T#..H",
    "H#H.T.#...####..#..H",
    "H######.F....#..####",
    "C#..#.#.FF..##....#C",
    "C#..#.#....##..CC.#C",
    "H#EE#.####S#.....##H",
    "H#EE#....#.#..T..#.H",
    "H#..######.######..H",
    "T#..#....#.#.....#.T",
    "H#..#.HH.#.#.FFF.#.H",
    "H####.HF.#.#.F.F.#.H",
    "H#.......#.#######.H",
    "F#.CC..T.#.......#.F",
    "H#.CC....#..EEE..#.H",
    "H#########..EE...###",
    "HH.FF.HH.####.....#H",
    "HHHHFFHHHHHHHTHHHHHH",
  };

  private CartesExemple() {}

  /** Remplit la carte (taille 20 attendue) avec le jardin d'exemple. */
  public static void remplirJardin(Carte carte) {
    carte.vider();
    for (int y = 0; y < JARDIN.length && y < carte.getTaille(); y++) {
      String ligne = JARDIN[y];
      for (int x = 0; x < ligne.length() && x < carte.getTaille(); x++) {
        TypeBloc t = depuisCaractere(ligne.charAt(x));
        if (t != null) {
          carte.placer(new Position(x, y), t);
        }
      }
    }
  }

  private static TypeBloc depuisCaractere(char c) {
    switch (c) {
      case '#':
        return TypeBloc.CHEMIN;
      case 'S':
        return TypeBloc.SPAWN;
      case 'C':
        return TypeBloc.CAILLOU;
      case 'H':
        return TypeBloc.HERBE;
      case 'F':
        return TypeBloc.FLEUR;
      case 'E':
        return TypeBloc.FLAQUE;
      case 'T':
        return TypeBloc.SOUCHE;
      case '.':
        return TypeBloc.HERBE; // jardin : les anciens trous deviennent de l'herbe
      default:
        return null;
    }
  }
}
