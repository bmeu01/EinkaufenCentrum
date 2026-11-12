package fr.jobas;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

public class Neud {

    private UUID idNeud;
    private float tauxAcide;
    private boolean capteurAcide;
    private TypeSalle type;
    private char accessibilite; 
    private int capaciteMax;
    private float tauxOccupation;
    private Statut statut;
    private List<Arret> arrets;

    public Neud(UUID idNeud, float tauxAcide, boolean capteurAcide, TypeSalle type, char accessibilite, int capaciteMax, float tauxOccupation, Statut statut, List<Arret> arrets) {
        this.idNeud = idNeud;
        this.tauxAcide = tauxAcide;
        this.capteurAcide = capteurAcide;
        this.type = type;
        this.accessibilite = accessibilite;
        this.capaciteMax = capaciteMax;
        this.tauxOccupation = tauxOccupation;
        this.statut = statut;
        this.arrets = (arrets != null) ? arrets : new ArrayList<>();
    }

    public UUID getIdNeud() {
        return idNeud;
    }

    public void setIdNeud(UUID idNeud) {
        this.idNeud = idNeud;
    }

    public float getTauxAcide() {
        return tauxAcide;
    }

    public void setTauxAcide(float tauxAcide) {
        this.tauxAcide = tauxAcide;
    }

    public boolean isCapteurAcide() {
        return capteurAcide;
    }

    public void setCapteurAcide(boolean capteurAcide) {
        this.capteurAcide = capteurAcide;
    }

    public TypeSalle getType() {
        return type;
    }

    public void setType(TypeSalle type) {
        this.type = type;
    }

    public char getAccessibilite() {
        return accessibilite;
    }

    public void setAccessibilite(char accessibilite) {
        this.accessibilite = accessibilite;
    }

    public int getCapaciteMax() {
        return capaciteMax;
    }

    public void setCapaciteMax(int capaciteMax) {
        this.capaciteMax = capaciteMax;
    }

    public float getTauxOccupation() {
        return tauxOccupation;
    }

    public void setTauxOccupation(float tauxOccupation) {
        this.tauxOccupation = tauxOccupation;
    }

    public Statut getStatut() {
        return statut;
    }

    public void setStatut(Statut statut) {
        this.statut = statut;
    }

    public List<Arret> getArrets() {
        return arrets;
    }

    public void setArrets(List<Arret> arrets) {
        this.arrets = arrets;
    }
}
