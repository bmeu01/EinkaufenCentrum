package fr.jobas.model;

import java.util.List;
import java.util.UUID;
import java.util.concurrent.ThreadLocalRandom;

public class Fourmis {
  TypeFourmis typeFourmis;
  UUID idFourmis;
  boolean aNourriture; 
  Racine position; 


  public Fourmis(TypeFourmis typefourmis, UUID idFourmis, Racine position){
    this.typeFourmis = typefourmis;
    this.idFourmis = idFourmis; 
    this.aNourriture = false; 
    this.position = position;
  } 

  public Racine changerPosition() {
    if (this.position instanceof Noeud) {
      Noeud noeud = (Noeud) this.position;
      List<Arete> aretes = noeud.getAretes();
      if (aretes != null && !aretes.isEmpty()) {
        int index = ThreadLocalRandom.current().nextInt(aretes.size());
        this.position = aretes.get(index);
      }
    } else if (this.position instanceof Arete) {
      Arete arete = (Arete) this.position;
      Noeud depart = arete.getDepart();
      Noeud arrive = arete.getArrive();
      if (depart != null && arrive != null) {
        this.position = ThreadLocalRandom.current().nextBoolean() ? depart : arrive;
      } else if (depart != null) {
        this.position = depart;
      } else if (arrive != null) {
        this.position = arrive;
      }
    }

    return this.position;
  }
}
