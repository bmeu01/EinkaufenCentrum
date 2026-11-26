package fr.jobas.fourmis.blender;

import java.io.BufferedWriter;
import java.io.IOException;
import java.io.OutputStreamWriter;
import java.io.Writer;
import java.net.InetSocketAddress;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Connexion TCP vers le script Blender (fourmis_blender.py). Tous les envois passent par un
 * thread dédié : l'interface JavaFX n'est jamais bloquée, même si Blender ne répond pas.
 */
public class BlenderClient implements AutoCloseable {

  public static final String HOTE = "127.0.0.1";
  public static final int PORT = 9877;

  private final ExecutorService envoi =
      Executors.newSingleThreadExecutor(
          r -> {
            Thread t = new Thread(r, "envoi-blender");
            t.setDaemon(true);
            return t;
          });

  private Socket socket;
  private Writer sortie;
  private volatile boolean connecte;

  /** Tente la connexion (1 s max). Le résultat arrive de façon asynchrone. */
  public CompletableFuture<Boolean> connecter() {
    return CompletableFuture.supplyAsync(
        () -> {
          fermerSocket();
          try {
            Socket s = new Socket();
            s.connect(new InetSocketAddress(HOTE, PORT), 1000);
            s.setTcpNoDelay(true);
            socket = s;
            sortie =
                new BufferedWriter(
                    new OutputStreamWriter(s.getOutputStream(), StandardCharsets.UTF_8));
            connecte = true;
          } catch (IOException e) {
            connecte = false;
          }
          return connecte;
        },
        envoi);
  }

  /** Envoie une ligne JSON. Sans effet si Blender n'est pas connecté. */
  public void envoyer(String ligneJson) {
    if (!connecte) {
      return;
    }
    envoi.execute(
        () -> {
          if (!connecte) {
            return;
          }
          try {
            sortie.write(ligneJson);
            sortie.write('\n');
            sortie.flush();
          } catch (IOException e) {
            connecte = false; // Blender fermé en cours de route
            fermerSocket();
          }
        });
  }

  public boolean estConnecte() {
    return connecte;
  }

  public void deconnecter() {
    envoi.execute(
        () -> {
          connecte = false;
          fermerSocket();
        });
  }

  private void fermerSocket() {
    try {
      if (socket != null) {
        socket.close();
      }
    } catch (IOException ignored) {
      // rien à faire
    }
    socket = null;
    sortie = null;
  }

  @Override
  public void close() {
    deconnecter();
    envoi.shutdown();
  }
}
