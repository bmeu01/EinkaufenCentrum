package fr.jobas;

import java.util.UUID;

/**
 * Arret
 */
public class Arret {
    private UUID arret;
    private float tauxAcide;
    private char accessibilite; 
    private int capaciteMax;
    private float tauxOccupation;
    private Statut statut;
    private float largeur;
    private float longueur;
    private int nbPheromones ;

    public Arret(UUID arret, float tauxAcide, char accessibilite, int capaciteMax, float tauxOccupation, Statut statut, float largeur, float longueur) {
        this.arret = arret;
        this.tauxAcide = tauxAcide;
        this.accessibilite = accessibilite;
        this.capaciteMax = capaciteMax;
        this.tauxOccupation = tauxOccupation;
        this.statut = statut;
        this.largeur = largeur;
        this.longueur = longueur;
    }

    public UUID getArret() {
        return arret;
    }

    public void setArret(UUID arret) {
        this.arret = arret;
    }

    public float getTauxAcide() {
        return tauxAcide;
    }

    public void setTauxAcide(float tauxAcide) {
        this.tauxAcide = tauxAcide;
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

    public float getLargeur() {
        return largeur;
    }

    public void setLargeur(float largeur) {
        this.largeur = largeur;
    }

    public float getLongueur() {
        return longueur;
    }

    public void setLongueur(float longueur) {
        this.longueur = longueur;
    }
}
