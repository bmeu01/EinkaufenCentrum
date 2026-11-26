package fr.jobas.simulation;

import java.util.UUID;

import fr.jobas.model.Fourmis;
import fr.jobas.model.TypeFourmis;
import fr.jobas.model.GameState;
import fr.jobas.model.Graph;
import fr.jobas.model.Noeud;
import fr.jobas.model.Nid;

// (déplacements, phéromones, logique par tick)
/** MoteurSimulation */
public class MoteurSimulation {

  Graph graph;
  GameState state;

  // Il nous faut tt info des fourmis (le nombre)
  // Le graph
  public MoteurSimulation(Graph graph, GameState state) {
    this.graph = graph;
    this.state = state;
  }

  public void startSim() {
    state = GameState.SIMULATION; 
    // Spawn ants in there nest
    // Give them the right team/color
    // Make the ants move and explore (chance to diverge or stay on path)
    for (Nid nid : graph.getNids()) {
      spawnAnts(nid);
    }
  }

  //Faire apparaitre les fourmis à la position du nid 
  void spawnAnts(Nid nid) {
    // spawn 5 ants
    for (int i = 0; i < 5; i++) {
      // UUID.randomUUID() = créer un nouveau UUID (unique)
      TypeFourmis type = TypeFourmis.EXPLORATRICE;
      UUID uuid = UUID.randomUUID();
      
      graph.ajouterFourmi(new Fourmis(type, uuid, nid));
    }
  }

  public void stopSim() {
    state = GameState.CONSTRUCTION;
  }
}