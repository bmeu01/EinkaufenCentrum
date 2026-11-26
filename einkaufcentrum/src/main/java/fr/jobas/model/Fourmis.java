package fr.jobas.model;

import java.util.UUID;

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

  public Racine changerPosition(){
    if this.position.isNeud {
      Racine newPosition; 
      for (Arete areteDuNoeud : noeud.getAretes()){  
         //choisir une arete (equiprobabilité) et affecter a newPosition
         this.position = newPosition;
      }
    }
    if this.position.isArete {
      for (Arete areteDuNoeud : noeud.getAretes()){  
          //choisir un neud  (equiprobabilité) et affecter a newPosition
          this.position = newPosition;
    }
    
    // Regarder ce qu'il ya dans les arete du neud dans lequel elle est 
    // S'engager dans l'arete 
    //rgarder si le neud est accessible 
    //rentrer dans le neud 
    return position;
  }
}
