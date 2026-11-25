package fr.jobas.simulation;

import fr.jobas.model.GameState;
import fr.jobas.model.Graph;

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
    //
  }

  void spawnAnts() {}

  public void stopSim() {
    state = GameState.CONSTRUCTION;
  }
}
