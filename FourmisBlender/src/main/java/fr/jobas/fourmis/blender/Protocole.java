package fr.jobas.fourmis.blender;

import fr.jobas.fourmis.model.Carte;
import fr.jobas.fourmis.model.Position;
import fr.jobas.fourmis.model.TypeBloc;
import fr.jobas.fourmis.simulation.Fourmi;
import java.util.List;
import java.util.Map;

/**
 * Messages envoyés à Blender : un objet JSON par ligne.
 *
 * <pre>
 * {"cmd":"carte","taille":20,"tick_ms":350,"spawn":[x,y],"blocs":[[x,y,"CHEMIN"],...]}
 * {"cmd":"fourmis","tick":12,"tick_ms":350,"fourmis":[[id,x,y],...]}
 * {"cmd":"stop"}
 * </pre>
 */
public final class Protocole {

  private Protocole() {}

  public static String carte(Carte carte, int tickMs) {
    StringBuilder sb = new StringBuilder(8192);
    sb.append("{\"cmd\":\"carte\",\"taille\":").append(carte.getTaille());
    sb.append(",\"tick_ms\":").append(tickMs);
    Position s = carte.getSpawn();
    sb.append(",\"spawn\":");
    if (s == null) {
      sb.append("null");
    } else {
      sb.append('[').append(s.getX()).append(',').append(s.getY()).append(']');
    }
    sb.append(",\"blocs\":[");
    boolean premier = true;
    for (Map.Entry<Position, TypeBloc> e : carte.getBlocs().entrySet()) {
      if (!premier) {
        sb.append(',');
      }
      premier = false;
      sb.append('[').append(e.getKey().getX()).append(',').append(e.getKey().getY());
      sb.append(",\"").append(e.getValue().name()).append("\"]");
    }
    return sb.append("]}").toString();
  }

  public static String fourmis(int tick, int tickMs, List<Fourmi> fourmis) {
    StringBuilder sb = new StringBuilder(64 + fourmis.size() * 16);
    sb.append("{\"cmd\":\"fourmis\",\"tick\":").append(tick);
    sb.append(",\"tick_ms\":").append(tickMs).append(",\"fourmis\":[");
    for (int i = 0; i < fourmis.size(); i++) {
      Fourmi f = fourmis.get(i);
      if (i > 0) {
        sb.append(',');
      }
      sb.append('[').append(f.getId()).append(',').append(f.getPosition().getX());
      sb.append(',').append(f.getPosition().getY()).append(']');
    }
    return sb.append("]}").toString();
  }

  public static String stop() {
    return "{\"cmd\":\"stop\"}";
  }
}
