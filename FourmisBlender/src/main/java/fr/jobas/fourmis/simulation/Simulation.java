package fr.jobas.fourmis.simulation;

import fr.jobas.fourmis.model.Carte;
import fr.jobas.fourmis.model.Position;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Random;

/**
 * Toute la logique de déplacement est ici, en Java. Blender ne fait qu'afficher.
 *
 * <p>À chaque tick, chaque fourmi va sur une case voisine praticable choisie au hasard. Pour un
 * mouvement plus naturel, elle évite le demi-tour quand elle a le choix, et garde parfois sa
 * direction (inertie). Une nouvelle fourmi sort du spawn tous les {@link #TICKS_ENTRE_SORTIES}
 * ticks jusqu'au nombre demandé.
 */
public class Simulation {

  public static final int TICKS_ENTRE_SORTIES = 2;

  private final Carte carte;
  private final int nbFourmisMax;
  private final Random random;
  private final double inertie;
  private final List<Fourmi> fourmis = new ArrayList<>();
  private int tick = 0;

  /**
   * @param carte la carte (une copie est faite, l'éditeur peut changer sans effet)
   * @param nbFourmisMax nombre de fourmis à faire sortir du spawn
   * @param inertie probabilité (0..1) de continuer tout droit quand c'est possible
   * @param graine graine aléatoire
   */
  public Simulation(Carte carte, int nbFourmisMax, double inertie, long graine) {
    if (carte.getSpawn() == null) {
      throw new IllegalStateException("La carte n'a pas de spawn");
    }
    this.carte = new Carte(carte);
    this.nbFourmisMax = nbFourmisMax;
    this.inertie = inertie;
    this.random = new Random(graine);
  }

  /** Fait avancer la simulation d'un pas. */
  public void tick() {
    tick++;
    for (Fourmi f : fourmis) {
      deplacer(f);
    }
    if (fourmis.size() < nbFourmisMax && (tick - 1) % TICKS_ENTRE_SORTIES == 0) {
      fourmis.add(new Fourmi(fourmis.size(), carte.getSpawn()));
    }
  }

  private void deplacer(Fourmi f) {
    List<Position> choix = carte.voisinsPraticables(f.getPosition());
    if (choix.isEmpty()) {
      return; // coincée : elle reste sur place
    }
    if (choix.size() > 1 && f.getPrecedente() != null) {
      choix.remove(f.getPrecedente()); // pas de demi-tour si on peut l'éviter
    }
    boolean aUneDirection = f.getDx() != 0 || f.getDy() != 0;
    Position devant = f.getPosition().decaler(f.getDx(), f.getDy());
    Position cible;
    if (aUneDirection && choix.contains(devant) && random.nextDouble() < inertie) {
      cible = devant;
    } else {
      cible = choix.get(random.nextInt(choix.size()));
    }
    f.deplacerVers(cible);
  }

  public List<Fourmi> getFourmis() {
    return Collections.unmodifiableList(fourmis);
  }

  public int getTick() {
    return tick;
  }

  public Carte getCarte() {
    return carte;
  }
}
