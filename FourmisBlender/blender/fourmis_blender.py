"""
FOURMIS — diorama 3D photoréaliste pour la simulation Java
==========================================================
Blender 4.2+ (testé sur 5.3). 100 % procédural, aucun fichier externe.

Ce script ne calcule AUCUN déplacement : il écoute le programme Java sur
127.0.0.1:9877 et affiche ce qu'il reçoit.
  * {"cmd":"carte", ...}   -> construit le diorama (scène "Fourmis_Simulation")
  * {"cmd":"fourmis", ...} -> position de chaque fourmi à ce pas
  * {"cmd":"stop"}         -> plus de nouvelles positions

Ce que contient le diorama
  * relief continu : buttes herbeuses, chemins tassés en ornières, terre meuble
  * arches naturelles (racines et pierre) au-dessus de certains couloirs
  * nid de fourmis rousses en aiguilles de pin, avec plusieurs entrées
  * eau : les flaques voisines fusionnent en un seul étang, avec berges boueuses,
    roseaux, massettes, nénuphars en fleur et lentilles d'eau
  * herbe dense multicolore, épis, trèfle, fleurs (marguerites, boutons d'or,
    campanules), feuilles mortes, brindilles, champignons, mousse sur les pierres
  * coupe du sol visible sur les côtés (strates), socle en noyer, plaque gravée
  * lumière de fin d'après-midi, profondeur de champ (effet maquette)
  * petits habitants mignons : fourmis aux grands yeux brillants, papillons qui
    volent, coccinelles, escargots, amanites à pois, fraises des bois, glands,
    gouttes de rosée et un petit panneau « FOURMILIÈRE » devant le nid

Caméras : panneau « Fourmis » dans la barre latérale de la vue 3D (touche N)
  Vue d'ensemble / Suivre une fourmi / Fourmi suivante / Vue cinéma.

Utilisation : onglet Scripting > ouvrir ce fichier > Run Script (Alt+P),
puis « Lancer la simulation » dans l'application Java.
Si l'animation est trop lente : QUALITE = "rapide" ci-dessous.
"""

import json
import math
import random
import socket
import time
import traceback

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector, noise

HOTE, PORT = "127.0.0.1", 9877
NOM_SCENE = "Fourmis_Simulation"
QUALITE = "haute"          # "haute" ou "rapide"
CELL = 1.0
SUBDIV = 8                 # sommets du terrain par case
NIVEAU_EAU = -0.06
FOND_EAU = -0.26
EPAISSEUR = 0.9
RETARD_PAS = 2.0           # retard de l'affichage, en pas de simulation
ECHELLE_FOURMI = 1.7       # > 1 : fourmis plus visibles que nature

HERBEUX = ("HERBE", "FLEUR", "SOUCHE")
PRATICABLES = ("CHEMIN", "SPAWN")


def Q(haute, rapide):
    return haute if QUALITE == "haute" else rapide


# =============================================================================
# Petits outils
# =============================================================================
def lin(hexc):
    h = hexc.lstrip("#")
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255.0
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return tuple(out)


def lin4(hexc):
    return lin(hexc) + (1.0,)


def smooth(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def sst(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def bruit_np(X, Y, z, echelle):
    xs, ys = (X * echelle).ravel(), (Y * echelle).ravel()
    return np.array([noise.noise((a, b, z)) for a, b in zip(xs, ys)]).reshape(np.shape(X))


def entree(node, nom, valeur):
    s = node.inputs.get(nom)
    if s is not None:
        try:
            s.default_value = valeur
        except Exception:
            pass


# =============================================================================
# Matériaux
# =============================================================================
def _ramp(nt, c0, c1, p0=0.3, p1=0.7):
    r = nt.nodes.new("ShaderNodeValToRGB")
    r.color_ramp.elements[0].position = p0
    r.color_ramp.elements[0].color = (*c0, 1)
    r.color_ramp.elements[1].position = p1
    r.color_ramp.elements[1].color = (*c1, 1)
    return r


def nouveau_mat(nom):
    mat = bpy.data.materials.get(nom)
    if mat is not None:
        bpy.data.materials.remove(mat)
    mat = bpy.data.materials.new(nom)
    mat.use_nodes = True
    return mat, mat.node_tree, mat.node_tree.nodes.get("Principled BSDF")


def _mousse(nt, b, couleur_base, force):
    """Mousse sur les faces tournées vers le ciel."""
    L, N = nt.links, nt.nodes
    geo = N.new("ShaderNodeNewGeometry")
    sep = N.new("ShaderNodeSeparateXYZ")
    L.new(geo.outputs["Normal"], sep.inputs[0])
    haut = N.new("ShaderNodeMapRange")
    entree(haut, "From Min", 0.35)
    entree(haut, "From Max", 0.9)
    L.new(sep.outputs["Z"], haut.inputs["Value"])
    tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeTexNoise")
    entree(nz, "Scale", 7.0)
    entree(nz, "Detail", 8.0)
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    tache = N.new("ShaderNodeMapRange")
    entree(tache, "From Min", 0.42)
    entree(tache, "From Max", 0.58)
    L.new(nz.outputs["Fac"], tache.inputs["Value"])
    m1 = N.new("ShaderNodeMath")
    m1.operation = 'MULTIPLY'
    L.new(haut.outputs["Result"], m1.inputs[0])
    L.new(tache.outputs["Result"], m1.inputs[1])
    m2 = N.new("ShaderNodeMath")
    m2.operation = 'MULTIPLY'
    L.new(m1.outputs[0], m2.inputs[0])
    m2.inputs[1].default_value = force
    nz2 = N.new("ShaderNodeTexNoise")
    entree(nz2, "Scale", 40.0)
    L.new(tc.outputs["Object"], nz2.inputs["Vector"])
    rm = _ramp(nt, lin("#2F4A16"), lin("#7A9A2E"), 0.3, 0.75)
    L.new(nz2.outputs["Fac"], rm.inputs["Fac"])
    mix = N.new("ShaderNodeMix")
    mix.data_type = 'RGBA'
    L.new(m2.outputs[0], mix.inputs[0])
    L.new(couleur_base, mix.inputs[6])
    L.new(rm.outputs["Color"], mix.inputs[7])
    L.new(mix.outputs[2], b.inputs["Base Color"])
    rr = N.new("ShaderNodeMapRange")
    entree(rr, "To Min", 0.7)
    entree(rr, "To Max", 0.95)
    L.new(m2.outputs[0], rr.inputs["Value"])
    L.new(rr.outputs["Result"], b.inputs["Roughness"])


def mat_simple(nom, c1, c2, rugo=0.6, echelle=5.0, bump=0.2, coat=0.0, sss=0.0,
               etirement=None, metal=0.0, mousse=0.0):
    mat, nt, b = nouveau_mat(nom)
    L = nt.links
    tc = nt.nodes.new("ShaderNodeTexCoord")
    vec = tc.outputs["Object"]
    if etirement:
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = etirement
        L.new(vec, mp.inputs["Vector"])
        vec = mp.outputs["Vector"]
    nz = nt.nodes.new("ShaderNodeTexNoise")
    entree(nz, "Scale", echelle)
    entree(nz, "Detail", 7.0)
    L.new(vec, nz.inputs["Vector"])
    r = _ramp(nt, lin(c1), lin(c2))
    L.new(nz.outputs["Fac"], r.inputs["Fac"])
    entree(b, "Roughness", rugo)
    entree(b, "Metallic", metal)
    entree(b, "Coat Weight", coat)
    entree(b, "Coat Roughness", 0.12)
    if sss > 0:
        entree(b, "Subsurface Weight", sss)
        entree(b, "Subsurface Scale", 0.02)
    if mousse > 0:
        _mousse(nt, b, r.outputs["Color"], mousse)
    else:
        L.new(r.outputs["Color"], b.inputs["Base Color"])
    if bump > 0:
        nb = nt.nodes.new("ShaderNodeTexNoise")
        entree(nb, "Scale", echelle * 9)
        entree(nb, "Detail", 9.0)
        L.new(vec, nb.inputs["Vector"])
        bp = nt.nodes.new("ShaderNodeBump")
        entree(bp, "Strength", bump)
        entree(bp, "Distance", 0.01)
        L.new(nb.outputs["Fac"], bp.inputs["Height"])
        L.new(bp.outputs["Normal"], b.inputs["Normal"])
    mat.diffuse_color = lin4(c1)
    return mat


def mat_teinte(nom, rugo=0.55, sss=0.0, gradient=False, coat=0.0, variation=0.25):
    """Couleur lue dans l'attribut 'teinte' de chaque objet (herbe, feuilles...)."""
    mat, nt, b = nouveau_mat(nom)
    L, N = nt.links, nt.nodes
    at = N.new("ShaderNodeAttribute")
    at.attribute_name = "teinte"
    tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeTexNoise")
    entree(nz, "Scale", 18.0)
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    var = N.new("ShaderNodeMapRange")
    entree(var, "To Min", 1.0 - variation)
    entree(var, "To Max", 1.0 + variation)
    L.new(nz.outputs["Fac"], var.inputs["Value"])
    m = N.new("ShaderNodeMix")
    m.data_type = 'RGBA'
    m.blend_type = 'MULTIPLY'
    m.inputs[0].default_value = 1.0
    L.new(at.outputs["Color"], m.inputs[6])
    L.new(var.outputs["Result"], m.inputs[7])
    sortie = m.outputs[2]
    if gradient:
        at2 = N.new("ShaderNodeAttribute")
        at2.attribute_name = "t"
        g = N.new("ShaderNodeMapRange")
        entree(g, "To Min", 0.28)
        entree(g, "To Max", 1.0)
        L.new(at2.outputs["Fac"], g.inputs["Value"])
        m2 = N.new("ShaderNodeMix")
        m2.data_type = 'RGBA'
        m2.blend_type = 'MULTIPLY'
        m2.inputs[0].default_value = 1.0
        L.new(sortie, m2.inputs[6])
        L.new(g.outputs["Result"], m2.inputs[7])
        sortie = m2.outputs[2]
    L.new(sortie, b.inputs["Base Color"])
    entree(b, "Roughness", rugo)
    entree(b, "Coat Weight", coat)
    if sss > 0:
        entree(b, "Subsurface Weight", sss)
        entree(b, "Subsurface Scale", 0.01)
    mat.diffuse_color = lin4("#6A7A3A")
    return mat


def mat_terrain():
    """Sol unique, mélange terre / herbe rase / boue / terre meuble selon 'sol'."""
    mat, nt, b = nouveau_mat("FR_Terrain")
    L, N = nt.links, nt.nodes
    tc = N.new("ShaderNodeTexCoord")
    obj = tc.outputs["Object"]

    def bruit(echelle, detail=6.0):
        n = N.new("ShaderNodeTexNoise")
        entree(n, "Scale", echelle)
        entree(n, "Detail", detail)
        L.new(obj, n.inputs["Vector"])
        return n

    def couleur(c1, c2, echelle):
        r = _ramp(nt, lin(c1), lin(c2), 0.3, 0.75)
        L.new(bruit(echelle).outputs["Fac"], r.inputs["Fac"])
        return r.outputs["Color"]

    terre = couleur("#4E3420", "#8C6A46", 2.2)
    vor = N.new("ShaderNodeTexVoronoi")
    entree(vor, "Scale", 32.0)
    L.new(obj, vor.inputs["Vector"])
    grav = N.new("ShaderNodeMapRange")
    entree(grav, "From Min", 0.0)
    entree(grav, "From Max", 0.11)
    entree(grav, "To Min", 0.9)
    entree(grav, "To Max", 0.0)
    L.new(vor.outputs["Distance"], grav.inputs["Value"])
    mg = N.new("ShaderNodeMix")
    mg.data_type = 'RGBA'
    L.new(grav.outputs["Result"], mg.inputs[0])
    L.new(terre, mg.inputs[6])
    mg.inputs[7].default_value = lin4("#A89A86")
    terre = mg.outputs[2]

    herbe = couleur("#2F4216", "#5A6A28", 2.5)
    boue = couleur("#241A12", "#3A2B1D", 6.0)
    meuble = couleur("#3A2A1C", "#5A4130", 8.0)

    at = N.new("ShaderNodeAttribute")
    at.attribute_name = "sol"
    sep = N.new("ShaderNodeSeparateColor")
    L.new(at.outputs["Color"], sep.inputs[0])
    casse = bruit(6.0, 5.0)

    def facteur(sortie):
        sub = N.new("ShaderNodeMath")
        sub.operation = 'SUBTRACT'
        L.new(casse.outputs["Fac"], sub.inputs[0])
        sub.inputs[1].default_value = 0.5
        mul = N.new("ShaderNodeMath")
        mul.operation = 'MULTIPLY'
        L.new(sub.outputs[0], mul.inputs[0])
        mul.inputs[1].default_value = 0.7
        add = N.new("ShaderNodeMath")
        add.operation = 'ADD'
        L.new(sortie, add.inputs[0])
        L.new(mul.outputs[0], add.inputs[1])
        mr = N.new("ShaderNodeMapRange")
        entree(mr, "From Min", 0.32)
        entree(mr, "From Max", 0.62)
        L.new(add.outputs[0], mr.inputs["Value"])
        return mr.outputs["Result"]

    def melange(f, a, c):
        m = N.new("ShaderNodeMix")
        m.data_type = 'RGBA'
        L.new(f, m.inputs[0])
        L.new(a, m.inputs[6])
        L.new(c, m.inputs[7])
        return m.outputs[2]

    f_boue = facteur(sep.outputs[2])
    c = melange(facteur(sep.outputs[0]), terre, herbe)
    alpha = at.outputs.get("Alpha")
    if alpha is not None:
        c = melange(facteur(alpha), c, meuble)
    c = melange(f_boue, c, boue)
    L.new(c, b.inputs["Base Color"])
    rug = N.new("ShaderNodeMapRange")
    entree(rug, "To Min", 0.93)
    entree(rug, "To Max", 0.28)
    L.new(f_boue, rug.inputs["Value"])
    L.new(rug.outputs["Result"], b.inputs["Roughness"])

    nb = bruit(55.0, 12.0)
    bp = N.new("ShaderNodeBump")
    entree(bp, "Strength", 0.7)
    entree(bp, "Distance", 0.008)
    L.new(nb.outputs["Fac"], bp.inputs["Height"])
    L.new(bp.outputs["Normal"], b.inputs["Normal"])
    mat.diffuse_color = lin4("#6E5235")
    return mat


def mat_strates():
    """Coupe du sol sur les côtés du plateau : humus, terre, argile, sable, graviers."""
    mat, nt, b = nouveau_mat("FR_Strates")
    L, N = nt.links, nt.nodes
    tc = N.new("ShaderNodeTexCoord")
    sep = N.new("ShaderNodeSeparateXYZ")
    L.new(tc.outputs["Object"], sep.inputs[0])
    nz = N.new("ShaderNodeTexNoise")
    entree(nz, "Scale", 2.0)
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    ondul = N.new("ShaderNodeMath")
    ondul.operation = 'MULTIPLY_ADD'
    L.new(nz.outputs["Fac"], ondul.inputs[0])
    ondul.inputs[1].default_value = 0.09
    L.new(sep.outputs["Z"], ondul.inputs[2])
    mr = N.new("ShaderNodeMapRange")
    entree(mr, "From Min", -EPAISSEUR)
    entree(mr, "From Max", 0.05)
    L.new(ondul.outputs[0], mr.inputs["Value"])
    rp = N.new("ShaderNodeValToRGB")
    cr = rp.color_ramp
    pts = [(0.0, "#6E6A62"), (0.18, "#8C8476"), (0.3, "#C2A475"), (0.48, "#A8683C"),
           (0.66, "#6A4529"), (0.86, "#3A2717"), (1.0, "#241810")]
    cr.elements[0].position, cr.elements[0].color = pts[0][0], lin4(pts[0][1])
    cr.elements[1].position, cr.elements[1].color = pts[-1][0], lin4(pts[-1][1])
    for p, c in pts[1:-1]:
        e = cr.elements.new(p)
        e.color = lin4(c)
    L.new(mr.outputs["Result"], rp.inputs["Fac"])
    vor = N.new("ShaderNodeTexVoronoi")
    entree(vor, "Scale", 24.0)
    L.new(tc.outputs["Object"], vor.inputs["Vector"])
    cail = N.new("ShaderNodeMapRange")
    entree(cail, "From Min", 0.0)
    entree(cail, "From Max", 0.14)
    entree(cail, "To Min", 0.7)
    entree(cail, "To Max", 0.0)
    L.new(vor.outputs["Distance"], cail.inputs["Value"])
    mix = N.new("ShaderNodeMix")
    mix.data_type = 'RGBA'
    L.new(cail.outputs["Result"], mix.inputs[0])
    L.new(rp.outputs["Color"], mix.inputs[6])
    mix.inputs[7].default_value = lin4("#9A938A")
    L.new(mix.outputs[2], b.inputs["Base Color"])
    entree(b, "Roughness", 0.92)
    nb = N.new("ShaderNodeTexNoise")
    entree(nb, "Scale", 60.0)
    entree(nb, "Detail", 10.0)
    L.new(tc.outputs["Object"], nb.inputs["Vector"])
    bp = N.new("ShaderNodeBump")
    entree(bp, "Strength", 0.6)
    L.new(nb.outputs["Fac"], bp.inputs["Height"])
    L.new(bp.outputs["Normal"], b.inputs["Normal"])
    return mat


def mat_bois_coupe():
    mat, nt, b = nouveau_mat("FR_Bois_Coupe")
    L = nt.links
    tc = nt.nodes.new("ShaderNodeTexCoord")
    wv = nt.nodes.new("ShaderNodeTexWave")
    try:
        wv.wave_type = 'RINGS'
        wv.rings_direction = 'Z'
    except Exception:
        pass
    entree(wv, "Scale", 9.0)
    entree(wv, "Distortion", 3.0)
    entree(wv, "Detail", 2.0)
    L.new(tc.outputs["Object"], wv.inputs["Vector"])
    r = _ramp(nt, lin("#7A5434"), lin("#C49B70"), 0.2, 0.8)
    L.new(wv.outputs["Fac"], r.inputs["Fac"])
    L.new(r.outputs["Color"], b.inputs["Base Color"])
    entree(b, "Roughness", 0.75)
    return mat


def mat_noyer():
    """Socle en noyer verni."""
    mat, nt, b = nouveau_mat("FR_Noyer")
    L = nt.links
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (0.4, 6.0, 1.0)
    L.new(tc.outputs["Object"], mp.inputs["Vector"])
    wv = nt.nodes.new("ShaderNodeTexWave")
    entree(wv, "Scale", 3.0)
    entree(wv, "Distortion", 6.0)
    entree(wv, "Detail", 4.0)
    L.new(mp.outputs["Vector"], wv.inputs["Vector"])
    r = _ramp(nt, lin("#24130A"), lin("#5A3418"), 0.25, 0.85)
    L.new(wv.outputs["Fac"], r.inputs["Fac"])
    L.new(r.outputs["Color"], b.inputs["Base Color"])
    entree(b, "Roughness", 0.35)
    entree(b, "Coat Weight", 0.8)
    entree(b, "Coat Roughness", 0.06)
    return mat


def mat_eau():
    mat, nt, b = nouveau_mat("FR_Eau")
    L = nt.links
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.noise_dimensions = '4D'
    nz.name = "Vaguelettes"
    entree(nz, "Scale", 7.0)
    entree(nz, "Detail", 4.0)
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    bp = nt.nodes.new("ShaderNodeBump")
    entree(bp, "Strength", 0.08)
    entree(bp, "Distance", 0.02)
    L.new(nz.outputs["Fac"], bp.inputs["Height"])
    L.new(bp.outputs["Normal"], b.inputs["Normal"])
    entree(b, "Base Color", lin4("#2E4A3A"))
    entree(b, "Roughness", 0.02)
    entree(b, "IOR", 1.33)
    entree(b, "Transmission Weight", 0.9)
    for attr, val in (("use_raytrace_refraction", True), ("surface_render_method", 'DITHERED'),
                      ("use_screen_refraction", True), ("refraction_depth", 0.15)):
        try:
            setattr(mat, attr, val)
        except Exception:
            pass
    mat.diffuse_color = lin4("#2A5A60")
    return mat


def materiaux():
    return {
        "terrain": mat_terrain(),
        "strates": mat_strates(),
        "noyer": mat_noyer(),
        "laiton": mat_simple("FR_Laiton", "#B08A3E", "#D8B45E", 0.28, 30.0, 0.05, metal=1.0),
        "grave": mat_simple("FR_Grave", "#1A140C", "#2A2016", 0.5, 10.0, 0.0),
        "table": mat_simple("FR_Table", "#E4D8C6", "#F0E6D8", 0.85, 0.8, 0.0),
        "herbe": mat_teinte("FR_Herbe", 0.5, 0.18, gradient=True, variation=0.18),
        "teinte": mat_teinte("FR_Vegetal", 0.6, 0.15),
        "feuille": mat_teinte("FR_Feuille", 0.62, 0.22, variation=0.3),
        "champignon": mat_teinte("FR_Champignon", 0.45, 0.25, coat=0.25, variation=0.12),
        "pierre": mat_simple("FR_Pierre", "#6E6A63", "#A8A296", 0.8, 3.0, 0.55, mousse=0.95),
        "gravier": mat_simple("FR_Gravier", "#6E6254", "#ADA090", 0.8, 6.0, 0.35),
        "motte": mat_simple("FR_Motte", "#2E2116", "#4E3826", 0.95, 9.0, 0.6),
        "ecorce": mat_simple("FR_Ecorce", "#2A1D13", "#5A4430", 0.92, 3.0, 0.9,
                             etirement=(4, 4, 0.5), mousse=0.7),
        "brindille": mat_simple("FR_Brindille", "#3A2C20", "#6E5A44", 0.85, 6.0, 0.5,
                                etirement=(1, 1, 0.2)),
        "bois": mat_bois_coupe(),
        "tige": mat_simple("FR_Tige", "#2C4614", "#4C6B24", 0.55, 8.0, 0.0, sss=0.12),
        "petale_blanc": mat_simple("FR_Petale_Blanc", "#E6E3DA", "#FFFFFF", 0.45, 9.0, 0.0, sss=0.35),
        "petale_jaune": mat_simple("FR_Petale_Jaune", "#E8B400", "#FFD83A", 0.22, 9.0, 0.0,
                                   sss=0.2, coat=0.5),
        "petale_mauve": mat_simple("FR_Petale_Mauve", "#7C5CB0", "#A88CD4", 0.45, 9.0, 0.0, sss=0.3),
        "nenuphar_fleur": mat_simple("FR_Nenuphar_Fleur", "#F2D6E2", "#FFF4F8", 0.4, 9.0, 0.0, sss=0.4),
        "coeur": mat_simple("FR_Coeur_Fleur", "#D08A10", "#F2C230", 0.7, 25.0, 0.5),
        "nenuphar": mat_simple("FR_Nenuphar", "#2C4A18", "#4C6E26", 0.25, 6.0, 0.05, coat=0.6),
        "eau": mat_eau(),
        "trou_nid": mat_simple("FR_Trou_Nid", "#050302", "#0C0806", 1.0, 5.0, 0.0),
        "chitine_noire": mat_simple("FR_Chitine_Noire", "#100806", "#2A160E", 0.3, 8.0, 0.06, coat=0.55),
        "chitine_rousse": mat_simple("FR_Chitine_Rousse", "#5A220E", "#8E3A18", 0.38, 8.0, 0.06,
                                     coat=0.4, sss=0.15),
        "pattes": mat_simple("FR_Pattes", "#2A120A", "#5A2A14", 0.45, 10.0, 0.0, coat=0.3),
        "oeil": mat_simple("FR_Oeil", "#050505", "#121212", 0.08, 30.0, 0.0, coat=1.0),
        "graine": mat_simple("FR_Graine", "#B08A52", "#E0C08A", 0.5, 20.0, 0.2, sss=0.1),
        **materiaux_mignons(),
    }


# =============================================================================
# Géométrie : lots (un objet par famille), gabarits, tubes
# =============================================================================
class Lot:
    """Accumule beaucoup de petites pièces dans un seul mesh (rapide à afficher)."""

    def __init__(self, nom):
        self.nom = nom
        self.V, self.F, self.Mi, self.Ls, self.C, self.T = [], [], [], [], [], []
        self.cles, self.n = [], 0

    def ajout(self, V, F, cle, C=None, T=None, lisse=True):
        V = np.asarray(V, dtype=np.float64).reshape(-1, 3)
        k = len(V)
        if k == 0:
            return
        if cle not in self.cles:
            self.cles.append(cle)
        mi = self.cles.index(cle)
        if isinstance(F, np.ndarray):
            Fl = (F + self.n).tolist()
        else:
            Fl = [[i + self.n for i in f] for f in F]
        self.V.append(V)
        self.F.extend(Fl)
        self.Mi.extend([mi] * len(Fl))
        self.Ls.extend([lisse] * len(Fl))
        if C is None:
            C = np.ones((k, 4))
        else:
            C = np.asarray(C, dtype=np.float64)
            if C.ndim == 1:
                C = np.tile(C, (k, 1))
        self.C.append(C.reshape(k, 4))
        self.T.append(np.ones(k) if T is None else np.asarray(T, dtype=np.float64).reshape(k))
        self.n += k

    def objet(self, sc, M):
        if not self.n:
            return None
        me = bpy.data.meshes.new("FR_" + self.nom)
        me.from_pydata(np.concatenate(self.V).tolist(), [], self.F)
        me.polygons.foreach_set("material_index", self.Mi)
        me.polygons.foreach_set("use_smooth", self.Ls)
        for c in self.cles:
            me.materials.append(M[c])
        ca = me.color_attributes.new("teinte", 'FLOAT_COLOR', 'POINT')
        ca.data.foreach_set("color", np.concatenate(self.C).astype(np.float32).ravel())
        at = me.attributes.new("t", 'FLOAT', 'POINT')
        at.data.foreach_set("value", np.concatenate(self.T).astype(np.float32))
        me.update()
        ob = bpy.data.objects.new(self.nom, me)
        sc.collection.objects.link(ob)
        return ob


_PRIM = {}


def _depuis_bm(bm):
    bm.verts.index_update()
    V = np.array([v.co[:] for v in bm.verts])
    F = [tuple(v.index for v in f.verts) for f in bm.faces]
    bm.free()
    return V, F


def prim(nom):
    if nom in _PRIM:
        return _PRIM[nom]
    bm = bmesh.new()
    if nom == "sphere":
        bmesh.ops.create_uvsphere(bm, u_segments=14, v_segments=9, radius=1.0)
    elif nom == "sphere_basse":
        bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=5, radius=1.0)
    elif nom == "dome":
        bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=1.0)
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -0.25], context='VERTS')
    elif nom == "disque":
        bmesh.ops.create_circle(bm, cap_ends=True, segments=16, radius=1.0)
    elif nom == "cylindre":
        bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=1, radius2=1, depth=1)
    elif nom == "nenuphar":
        c = bm.verts.new((0, 0, 0))
        ring = []
        for i in range(21):
            a = 0.32 + i * (math.tau - 0.38) / 20
            ring.append(bm.verts.new((math.cos(a), math.sin(a), 0.02 * math.sin(i))))
        for i in range(20):
            bm.faces.new((c, ring[i], ring[i + 1]))
    _PRIM[nom] = _depuis_bm(bm)
    return _PRIM[nom]


def rocher(graine, sub=3):
    cle = ("rocher", graine, sub)
    if cle in _PRIM:
        return _PRIM[cle]
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
    s = Vector((graine * 7.31, graine * 3.17, graine * 5.53))
    for v in bm.verts:
        p = v.co.copy()
        k = 1 + 0.3 * noise.noise(p * 1.3 + s) + 0.08 * noise.noise(p * 4.5 + s)
        q = p * k
        if q.z < -0.3:
            q.z = -0.3 + (q.z + 0.3) * 0.2
        v.co = q
    _PRIM[cle] = _depuis_bm(bm)
    return _PRIM[cle]


def xf(V, M):
    A = np.array(M)
    return V @ A[:3, :3].T + A[:3, 3]


def mat4(loc=(0, 0, 0), rz=0.0, rx=0.0, ry=0.0, ech=(1, 1, 1)):
    return (Matrix.Translation(Vector(loc)) @ Matrix.Rotation(rz, 4, 'Z')
            @ Matrix.Rotation(ry, 4, 'Y') @ Matrix.Rotation(rx, 4, 'X')
            @ Matrix.Diagonal((*ech, 1.0)))


def inst(lot, gab, M, cle, C=None, lisse=True):
    V, F = gab
    lot.ajout(xf(V, M), F, cle, C=C, lisse=lisse)


def tube(P, R, seg=8, rugueux=0.0, graine=0.0, bouts=True):
    """Tube lisse le long d'une polyligne P (k,3), rayons R (k,)."""
    P = np.asarray(P, dtype=np.float64)
    R = np.asarray(R, dtype=np.float64)
    k = len(P)
    T = np.gradient(P, axis=0)
    T /= np.linalg.norm(T, axis=1)[:, None] + 1e-9
    ref = np.array([0.0, 0.0, 1.0]) if abs(T[0][2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    N = [np.cross(T[0], ref)]
    N[0] /= np.linalg.norm(N[0])
    for i in range(1, k):
        n = N[-1] - np.dot(N[-1], T[i]) * T[i]
        N.append(n / (np.linalg.norm(n) + 1e-9))
    N = np.array(N)
    B = np.cross(T, N)
    a = np.linspace(0, math.tau, seg, endpoint=False)
    D = np.cos(a)[None, :, None] * N[:, None, :] + np.sin(a)[None, :, None] * B[:, None, :]
    Rv = np.repeat(R[:, None], seg, axis=1)
    if rugueux > 0:
        pts = P[:, None, :] + D * Rv[:, :, None]
        for i in range(k):
            for j in range(seg):
                x, y, z = pts[i, j] * 3.0
                Rv[i, j] *= 1 + rugueux * noise.noise((x + graine, y, z))
    V = (P[:, None, :] + D * Rv[:, :, None]).reshape(-1, 3)
    F = [(i * seg + j, i * seg + (j + 1) % seg, (i + 1) * seg + (j + 1) % seg, (i + 1) * seg + j)
         for i in range(k - 1) for j in range(seg)]
    if bouts:
        V = np.vstack([V, P[0], P[-1]])
        c0, c1 = len(V) - 2, len(V) - 1
        F += [(c0, (j + 1) % seg, j) for j in range(seg)]
        F += [(c1, (k - 1) * seg + j, (k - 1) * seg + (j + 1) % seg) for j in range(seg)]
    return V, F


# =============================================================================
# Carte, champs et relief
# =============================================================================
class Etat:
    taille = 20
    carte = {}
    spawn = None
    masques = {}
    H = None
    trous_nid = []
    fourmi = None
    fourmis = {}
    tick_s = 0.35
    noeud_eau = None
    derniere = time.perf_counter()
    mode = "ensemble"
    suivie = 0
    angle = 0.0
    regard = None
    scene = NOM_SCENE
    papillons = []


def monde(x, y):
    n = Etat.taille
    return Vector(((x - (n - 1) / 2) * CELL, ((n - 1) / 2 - y) * CELL, 0.0))


def preparer_masques():
    n = Etat.taille
    T = [[Etat.carte.get((x, y)) for x in range(n)] for y in range(n)]

    def m(test):
        return np.array([[test(T[y][x]) for x in range(n)] for y in range(n)], dtype=bool)
    Etat.masques = {
        "herbe": m(lambda t: t in HERBEUX),
        "chemin": m(lambda t: t in PRATICABLES),
        "caillou": m(lambda t: t == "CAILLOU"),
        "trou": m(lambda t: t is None),
        "eau": m(lambda t: t == "FLAQUE"),
    }
    Etat.trous_nid = []
    if Etat.spawn is not None:
        c = monde(*Etat.spawn)
        Etat.trous_nid = [(c.x, c.y, 0.14, 0.075), (c.x + 0.3, c.y + 0.12, 0.09, 0.05),
                          (c.x - 0.18, c.y - 0.28, 0.08, 0.045)]


def blobs(X, Y, masque, rayon):
    """Somme de « metaballs » centrées sur les cases du masque : deux cases voisines
    se fondent en une seule forme (c'est ainsi que les flaques fusionnent)."""
    n = masque.shape[0]
    X = np.asarray(X, dtype=np.float64)
    Y = np.asarray(Y, dtype=np.float64)
    cx0 = np.clip(np.floor(X / CELL + n / 2).astype(int), 0, n - 1)
    cy0 = np.clip(np.floor(n / 2 - Y / CELL).astype(int), 0, n - 1)
    F = np.zeros_like(X)
    r = int(math.ceil(rayon))
    for ox in range(-r, r + 1):
        for oy in range(-r, r + 1):
            cx, cy = cx0 + ox, cy0 + oy
            ok = (cx >= 0) & (cx < n) & (cy >= 0) & (cy < n)
            mk = masque[np.clip(cy, 0, n - 1), np.clip(cx, 0, n - 1)] & ok
            wx = (cx - (n - 1) / 2) * CELL
            wy = ((n - 1) / 2 - cy) * CELL
            d2 = ((X - wx) ** 2 + (Y - wy) ** 2) / (rayon * CELL) ** 2
            F += np.where(mk, np.clip(1 - d2, 0, None) ** 2, 0.0)
    return F


def champs(X, Y):
    M = Etat.masques
    Wh = blobs(X, Y, M["herbe"], 0.8)
    Wp = blobs(X, Y, M["chemin"], 0.8)
    Wk = blobs(X, Y, M["caillou"], 0.8)
    Wt = blobs(X, Y, M["trou"], 0.8)
    We = blobs(X, Y, M["eau"], 0.8)
    S = Wh + Wp + Wk + Wt + We + 1e-6
    Wh, Wp, Wk, Wt = Wh / S, Wp / S, Wk / S, Wt / S
    Fe = blobs(X, Y, M["eau"], 1.0)
    return Wh, Wp, Wk, Wt, Fe


def relief(X, Y):
    """Hauteur du sol + poids des sols pour le matériau."""
    Wh, Wp, Wk, Wt, Fe = champs(X, Y)
    b1 = bruit_np(X, Y, 1.7, 0.3)
    b2 = bruit_np(X, Y, 4.1, 1.1)
    b3 = bruit_np(X, Y, 7.3, 4.5)
    b4 = np.abs(bruit_np(X, Y, 9.9, 9.0))
    h = 0.05 * b1 + 0.018 * b2 + 0.006 * b3
    h += Wh * (0.06 + 0.04 * b2)                      # buttes herbeuses
    h += Wk * (0.04 + 0.02 * b2)                      # zones rocheuses
    h -= Wp * (0.028 + 0.012 * b3)                    # chemins tassés
    h += Wt * (-0.055 + 0.035 * b4)                   # terre meuble, mottes
    berge = sst(0.06, 0.24, Fe)
    h = h * (1 - berge) + np.maximum(h, NIVEAU_EAU + 0.035) * berge   # berges hors de l'eau
    h += 0.03 * sst(0.05, 0.3, Fe) * (1 - sst(0.3, 0.6, Fe))   # petit bourrelet de berge
    ew = sst(0.28, 0.85, Fe + 0.07 * b2)
    h = h * (1 - ew) + (FOND_EAU + 0.03 * b3) * ew
    if Etat.spawn is not None:
        c = monde(*Etat.spawn)
        dS = np.hypot(X - c.x, Y - c.y)
        h += 0.5 * 0.5 * (1 + np.cos(np.pi * np.clip(dS / 1.15, 0, 1))) * (1 + 0.12 * b3)
        for (tx, ty, prof, r) in Etat.trous_nid:
            h -= prof * np.exp(-((np.hypot(X - tx, Y - ty)) / r) ** 2)
    boue = sst(0.08, 0.45, Fe)
    sol = np.stack([Wh, Wp + Wk, boue, Wt], -1)
    return h, Fe, sol


def hauteur(px, py):
    """Hauteur du sol (interpolée dans la grille du terrain)."""
    H = Etat.H
    if H is None:
        return 0.0
    R = H.shape[0] - 1
    demi = Etat.taille * CELL / 2
    fx = min(max((px + demi) / (2 * demi) * R, 0.0), R - 1e-6)
    fy = min(max((py + demi) / (2 * demi) * R, 0.0), R - 1e-6)
    i, j = int(fx), int(fy)
    u, v = fx - i, fy - j
    return ((H[j, i] * (1 - u) + H[j, i + 1] * u) * (1 - v)
            + (H[j + 1, i] * (1 - u) + H[j + 1, i + 1] * u) * v)


def hauteur_np(X, Y):
    H = Etat.H
    R = H.shape[0] - 1
    demi = Etat.taille * CELL / 2
    fx = np.clip((np.asarray(X) + demi) / (2 * demi) * R, 0, R - 1e-6)
    fy = np.clip((np.asarray(Y) + demi) / (2 * demi) * R, 0, R - 1e-6)
    i, j = fx.astype(int), fy.astype(int)
    u, v = fx - i, fy - j
    return ((H[j, i] * (1 - u) + H[j, i + 1] * u) * (1 - v)
            + (H[j + 1, i] * (1 - u) + H[j + 1, i + 1] * u) * v)


def construire_terrain_mesh(sc, M):
    n = Etat.taille
    R = n * SUBDIV
    demi = n * CELL / 2
    xs = np.linspace(-demi, demi, R + 1)
    X, Y = np.meshgrid(xs, xs)
    H, Fe, sol = relief(X, Y)
    Etat.H = H
    Etat.Fe_grille = Fe
    idx = np.arange((R + 1) * (R + 1)).reshape(R + 1, R + 1)
    Fq = np.stack([idx[:-1, :-1], idx[:-1, 1:], idx[1:, 1:], idx[1:, :-1]], -1).reshape(-1, 4)
    V = np.stack([X, Y, H], -1).reshape(-1, 3)
    bord = ([idx[0, i] for i in range(R + 1)] + [idx[j, R] for j in range(1, R + 1)]
            + [idx[R, i] for i in range(R - 1, -1, -1)] + [idx[j, 0] for j in range(R - 1, 0, -1)])
    nb = len(V)
    bas = V[bord].copy()
    bas[:, 2] = -EPAISSEUR
    V = np.vstack([V, bas])
    faces = Fq.tolist()
    mi = [0] * len(faces)
    for k in range(len(bord)):
        a, b = k, (k + 1) % len(bord)
        faces.append([bord[b], bord[a], nb + a, nb + b])
        mi.append(1)
    faces.append([nb + k for k in range(len(bord) - 1, -1, -1)])
    mi.append(1)
    me = bpy.data.meshes.new("FR_terrain")
    me.from_pydata(V.tolist(), [], faces)
    me.polygons.foreach_set("material_index", mi)
    me.polygons.foreach_set("use_smooth", [m == 0 for m in mi])
    me.materials.append(M["terrain"])
    me.materials.append(M["strates"])
    ca = me.color_attributes.new("sol", 'FLOAT_COLOR', 'POINT')
    S = np.vstack([sol.reshape(-1, 4), np.tile([0, 1, 0, 0], (len(bord), 1))])
    ca.data.foreach_set("color", S.astype(np.float32).ravel())
    me.update()
    ob = bpy.data.objects.new("Terrain", me)
    sc.collection.objects.link(ob)

    # nappe d'eau unique sur tous les bassins
    masque = (Fe > 0.2)
    q = masque[:-1, :-1] | masque[:-1, 1:] | masque[1:, 1:] | masque[1:, :-1]
    Fw = Fq[q.ravel()]
    if len(Fw):
        utiles, inv = np.unique(Fw.ravel(), return_inverse=True)
        Vw = np.stack([X, Y, np.full_like(X, NIVEAU_EAU)], -1).reshape(-1, 3)[utiles]
        me = bpy.data.meshes.new("FR_eau")
        me.from_pydata(Vw.tolist(), [], inv.reshape(-1, 4).tolist())
        me.materials.append(M["eau"])
        ob = bpy.data.objects.new("Eau", me)
        sc.collection.objects.link(ob)
    Etat.noeud_eau = M["eau"].node_tree.nodes.get("Vaguelettes")


# =============================================================================
# Végétation et décor
# =============================================================================
PAL_HERBE = np.array([lin4(c) for c in ("#3E6A1A", "#52802A", "#6A9636", "#86A23E", "#A5A458", "#BCA66A")])
P_HERBE = np.array([0.22, 0.27, 0.22, 0.14, 0.09, 0.06])
PAL_ROSEAU = np.array([lin4(c) for c in ("#3C5A1E", "#4E6A26", "#6A7A34", "#8A8A4A")])
P_ROSEAU = np.array([0.3, 0.35, 0.25, 0.1])
PAL_FEUILLE = np.array([lin4(c) for c in ("#C2601C", "#8E3A18", "#D6A034", "#6E4824", "#8C7A36", "#A8441C")])
PAL_AIGUILLE = np.array([lin4(c) for c in ("#6A2E12", "#8A3E1A", "#4E2410", "#A2552A", "#5E4636", "#7A3A1C")])
PAL_CHAMPI = np.array([lin4(c) for c in ("#7A4A26", "#9A6234", "#B58A5A", "#5A3A22", "#C26A3A")])


def brins(X, Y, Z, rng, hmin, hmax, wmin=0.009, wmax=0.02, pench=(0.08, 0.5),
          pal=PAL_HERBE, prob=P_HERBE):
    N = len(X)
    h = rng.uniform(hmin, hmax, N)
    a = rng.uniform(0, math.tau, N)
    dx, dy = np.cos(a), np.sin(a)
    wa = a + math.pi / 2 + rng.uniform(-0.5, 0.5, N)
    px, py = np.cos(wa), np.sin(wa)
    pe = rng.uniform(*pench, N) * h
    w0 = rng.uniform(wmin, wmax, N)
    t = np.linspace(0, 1, 5)
    r = pe[:, None] * t ** 2
    z = h[:, None] * t * (1 - 0.18 * t ** 2)
    w = w0[:, None] * (1 - t) ** 0.7 + 0.0005
    cx = X[:, None] + dx[:, None] * r
    cy = Y[:, None] + dy[:, None] * r
    cz = Z[:, None] + z
    G = np.stack([cx + px[:, None] * w / 2, cy + py[:, None] * w / 2, cz], -1)
    D = np.stack([cx - px[:, None] * w / 2, cy - py[:, None] * w / 2, cz], -1)
    V = np.stack([G, D], 2).reshape(N * 10, 3)
    base = (np.arange(N) * 10)[:, None, None]
    q = np.array([[0, 1, 3, 2], [2, 3, 5, 4], [4, 5, 7, 6], [6, 7, 9, 8]])
    F = (base + q[None]).reshape(-1, 4)
    T = np.tile(np.repeat(t, 2), N)
    C = np.repeat(pal[rng.choice(len(pal), N, p=prob)], 10, axis=0)
    pointes = (V.reshape(N, 10, 3)[:, 8] + V.reshape(N, 10, 3)[:, 9]) / 2
    return V, F, T, C, pointes, h


def points_case(x, y, k, rng, etendue=0.52):
    c = monde(x, y)
    return (c.x + rng.uniform(-etendue, etendue, k), c.y + rng.uniform(-etendue, etendue, k))


def pres_du_nid(X, Y, rayon=1.0):
    if Etat.spawn is None:
        return np.zeros_like(X, dtype=bool)
    c = monde(*Etat.spawn)
    return np.hypot(X - c.x, Y - c.y) < rayon


def construire_herbe(lot, divers, rng):
    n = Etat.taille
    dens = {"HERBE": Q(300, 130), "FLEUR": Q(170, 75), "SOUCHE": Q(130, 60),
            "CAILLOU": Q(60, 25), None: Q(18, 8)}
    Xs, Ys, bord = [], [], []
    for y in range(n):
        for x in range(n):
            t = Etat.carte.get((x, y))
            if t == "FLAQUE":
                continue
            if t in PRATICABLES:
                k, est_bord = Q(70, 30), True
            else:
                k, est_bord = dens.get(t, 0), False
            if k:
                X, Y = points_case(x, y, k, rng)
                Xs.append(X)
                Ys.append(Y)
                bord.append(np.full(k, est_bord))
    X, Y, bord = np.concatenate(Xs), np.concatenate(Ys), np.concatenate(bord)
    Wh, Wp, Wk, Wt, Fe = champs(X, Y)
    garde = (Fe < 0.16) & ~pres_du_nid(X, Y, 1.12)
    garde &= ~bord | (Wh + 0.25 * rng.random(len(X)) > 0.38)     # bords de chemin envahis
    X, Y = X[garde], Y[garde]
    Z = hauteur_np(X, Y) - 0.012
    V, F, T, C, pointes, h = brins(X, Y, Z, rng, 0.12, 0.46)
    lot.ajout(V, F, "herbe", C, T)
    # petites pousses éparses sur les chemins
    Xs, Ys = [], []
    for (x, y), t in Etat.carte.items():
        if t == "CHEMIN":
            X2, Y2 = points_case(x, y, Q(7, 3), rng, 0.5)
            Xs.append(X2)
            Ys.append(Y2)
    if Xs:
        X2, Y2 = np.concatenate(Xs), np.concatenate(Ys)
        ok = ~pres_du_nid(X2, Y2, 1.15)
        X2, Y2 = X2[ok], Y2[ok]
        V2, F2, T2, C2, _p, _h = brins(X2, Y2, hauteur_np(X2, Y2) - 0.005, rng, 0.03, 0.1, 0.006, 0.012)
        lot.ajout(V2, F2, "herbe", C2, T2)
    # épis sur les brins les plus hauts
    choix = np.where((h > 0.38) & (rng.random(len(h)) < 0.09))[0]
    gab = prim("sphere_basse")
    for i in choix:
        p = pointes[i]
        inst(divers, gab, mat4(p + np.array([0, 0, 0.02]), rz=rng.uniform(0, 6.3),
                               rx=rng.uniform(-0.3, 0.3), ech=(0.007, 0.007, 0.03)),
             "teinte", C=lin4("#9A8A58"))
    # trèfle dans l'herbe
    gab = prim("sphere_basse")
    for y in range(n):
        for x in range(n):
            if Etat.carte.get((x, y)) == "HERBE" and rng.random() < 0.5:
                cx, cy = points_case(x, y, 3, rng, 0.4)
                for px, py in zip(cx, cy):
                    z = hauteur(px, py) + 0.035
                    for k in range(3):
                        a = k * math.tau / 3 + rng.uniform(0, 0.3)
                        inst(divers, gab, mat4((px + 0.018 * math.cos(a), py + 0.018 * math.sin(a), z),
                                               rz=a, ech=(0.02, 0.017, 0.003)),
                             "teinte", C=lin4("#3E6A22"))


def construire_roseaux(lot, divers, rng):
    """Roseaux et massettes le long des berges."""
    n = Etat.taille
    demi = n * CELL / 2
    pas = 0.16
    g = np.arange(-demi + pas / 2, demi, pas)
    X, Y = np.meshgrid(g, g)
    X, Y = X.ravel(), Y.ravel()
    Wh, Wp, Wk, Wt, Fe = champs(X, Y)
    rive = (Fe > 0.12) & (Fe < 0.34) & (Wp < 0.45) & (rng.random(len(X)) < 0.45)
    X, Y = X[rive], Y[rive]
    if not len(X):
        return
    k = 7
    Xr = np.repeat(X, k) + rng.normal(0, 0.035, len(X) * k)
    Yr = np.repeat(Y, k) + rng.normal(0, 0.035, len(X) * k)
    Zr = hauteur_np(Xr, Yr) - 0.01
    V, F, T, C, pointes, h = brins(Xr, Yr, Zr, rng, 0.45, 0.95, 0.007, 0.014, (0.02, 0.14),
                                   PAL_ROSEAU, P_ROSEAU)
    lot.ajout(V, F, "herbe", C, T)
    for i in range(0, len(X)):
        if rng.random() < 0.35:
            x, y = X[i] + rng.normal(0, 0.02), Y[i] + rng.normal(0, 0.02)
            z0 = hauteur(x, y)
            hh = rng.uniform(0.6, 0.85)
            dx, dy = rng.normal(0, 0.03, 2)
            Vt, Ft = tube([(x, y, z0), (x + dx * 0.5, y + dy * 0.5, z0 + hh * 0.5),
                           (x + dx, y + dy, z0 + hh)], [0.006, 0.005, 0.004], 6)
            divers.ajout(Vt, Ft, "tige")
            Vt, Ft = tube([(x + dx, y + dy, z0 + hh - 0.17), (x + dx, y + dy, z0 + hh - 0.03)],
                          [0.019, 0.02], 10)
            divers.ajout(Vt, Ft, "teinte", C=lin4("#4A2A14"))


def construire_rochers(lot, rng):
    n = Etat.taille
    gros = [rocher(i, 3) for i in range(5)]
    petits = [rocher(10 + i, 1) for i in range(6)]
    for (x, y), t in Etat.carte.items():
        c = monde(x, y)
        if t == "CAILLOU":
            s = rng.uniform(0.3, 0.4)
            px, py = c.x + rng.uniform(-0.08, 0.08), c.y + rng.uniform(-0.08, 0.08)
            inst(lot, gros[rng.integers(5)],
                 mat4((px, py, hauteur(px, py) - 0.06), rz=rng.uniform(0, 6.3),
                      rx=rng.uniform(-0.15, 0.15), ech=(s, s * rng.uniform(0.75, 0.95), s * rng.uniform(0.55, 0.8))),
                 "pierre")
            for _ in range(rng.integers(2, 4)):
                a, d = rng.uniform(0, 6.3), rng.uniform(0.25, 0.42)
                px, py = c.x + d * math.cos(a), c.y + d * math.sin(a)
                s = rng.uniform(0.07, 0.15)
                inst(lot, gros[rng.integers(5)],
                     mat4((px, py, hauteur(px, py) - 0.03), rz=rng.uniform(0, 6.3), ech=(s, s * 0.9, s * 0.7)),
                     "pierre")
        elif t in PRATICABLES or t is None:
            k = Q(9, 4) if t in PRATICABLES else Q(5, 2)
            X, Y = points_case(x, y, k, rng, 0.48)
            for px, py in zip(X, Y):
                s = rng.uniform(0.012, 0.038)
                inst(lot, petits[rng.integers(6)],
                     mat4((px, py, hauteur(px, py) - 0.3 * s), rz=rng.uniform(0, 6.3), ech=(s, s * 0.85, s * 0.6)),
                     "gravier" if t in PRATICABLES else "motte")
        elif t == "FLAQUE":
            X, Y = points_case(x, y, 5, rng, 0.4)
            for px, py in zip(X, Y):
                s = rng.uniform(0.03, 0.07)
                inst(lot, petits[rng.integers(6)],
                     mat4((px, py, hauteur(px, py) - 0.01), rz=rng.uniform(0, 6.3), ech=(s, s, s * 0.5)),
                     "gravier")


def fleur(lot, x, y, espece, rng):
    z0 = hauteur(x, y) - 0.01
    h = rng.uniform(0.22, 0.42)
    dx, dy = rng.normal(0, 0.035, 2)
    top = np.array([x + dx, y + dy, z0 + h])
    V, F = tube([(x, y, z0), (x + dx * 0.3, y + dy * 0.3, z0 + h * 0.5), tuple(top)],
                [0.007, 0.006, 0.005], 6)
    lot.ajout(V, F, "tige")
    for k in range(2):                                   # deux feuilles à la base
        a = rng.uniform(0, 6.3)
        inst(lot, prim("sphere_basse"),
             mat4((x + 0.04 * math.cos(a), y + 0.04 * math.sin(a), z0 + 0.03), rz=a,
                  ry=-0.4, ech=(0.05, 0.016, 0.003)), "tige")
    gab = prim("sphere_basse")
    if espece == "bouton_or":
        for i in range(5):
            a = i * math.tau / 5
            c = top + np.array([0.016 * math.cos(a), 0.016 * math.sin(a), 0.008])
            inst(lot, gab, mat4(c, rz=a, ry=-0.65, ech=(0.02, 0.017, 0.004)), "petale_jaune")
        inst(lot, gab, mat4(top + np.array([0, 0, 0.008]), ech=(0.009, 0.009, 0.007)), "coeur")
    else:
        nb = 14 if espece == "marguerite" else 9
        lg = 0.034 if espece == "marguerite" else 0.03
        cle = "petale_blanc" if espece == "marguerite" else "petale_mauve"
        for i in range(nb):
            a = i * math.tau / nb
            c = top + np.array([lg * math.cos(a), lg * math.sin(a), 0.003])
            inst(lot, gab, mat4(c, rz=a, ry=0.12, ech=(lg, 0.008, 0.0028)), cle)
        inst(lot, gab, mat4(top + np.array([0, 0, 0.006]), ech=(0.015, 0.015, 0.009)), "coeur")


def construire_fleurs(lot, rng):
    especes = ["marguerite", "bouton_or", "campanule"]
    for (x, y), t in Etat.carte.items():
        if t == "FLEUR":
            k = Q(7, 4)
        elif t == "HERBE":
            k = 1 if rng.random() < 0.35 else 0
        else:
            continue
        sp = especes[(x * 3 + y) % 3] if t == "FLEUR" else especes[rng.integers(3)]
        X, Y = points_case(x, y, k, rng, 0.4)
        for px, py in zip(X, Y):
            fleur(lot, px, py, sp if rng.random() < 0.75 else especes[rng.integers(3)], rng)


def champignon(lot, x, y, taille, rng, z=None):
    z0 = hauteur(x, y) - 0.01 if z is None else z
    h = taille * rng.uniform(0.8, 1.3)
    dx, dy = rng.normal(0, 0.12 * taille, 2)
    top = np.array([x + dx, y + dy, z0 + h])
    V, F = tube([(x, y, z0), (x + dx * 0.4, y + dy * 0.4, z0 + h * 0.5), tuple(top)],
                [0.18 * taille, 0.14 * taille, 0.12 * taille], 8)
    lot.ajout(V, F, "champignon", C=lin4("#D8CBB0"))
    r = taille * rng.uniform(0.45, 0.7)
    col = PAL_CHAMPI[rng.integers(len(PAL_CHAMPI))]
    inst(lot, prim("dome"), mat4(top, rz=rng.uniform(0, 6.3), ech=(r, r, r * 0.65)),
         "champignon", C=col)
    inst(lot, prim("disque"), mat4(top - np.array([0, 0, r * 0.15]), ech=(r * 0.95, r * 0.95, 1)),
         "champignon", C=lin4("#C8B89A"))


def construire_souches(lot, divers, rng):
    gab = prim("sphere_basse")
    for (x, y), t in Etat.carte.items():
        if t != "SOUCHE":
            continue
        c = monde(x, y)
        cx, cy = c.x + rng.uniform(-0.06, 0.06), c.y + rng.uniform(-0.06, 0.06)
        z0 = hauteur(cx, cy) - 0.05
        h = rng.uniform(0.3, 0.48)
        seg, rangs = 30, 9
        s = float(rng.uniform(0, 50))
        anneaux = []
        for k in range(rangs + 1):
            z = h * k / rangs
            rr = 0.23 + 0.09 * (1 - z / h) ** 4
            for i in range(seg):
                a = i * math.tau / seg
                ride = 1 + 0.07 * noise.noise((math.cos(a) * 3, math.sin(a) * 3, z * 12 + s))
                anneaux.append((cx + rr * ride * math.cos(a), cy + rr * ride * math.sin(a), z0 + z))
        V = np.array(anneaux)
        F = [(k * seg + i, k * seg + (i + 1) % seg, (k + 1) * seg + (i + 1) % seg, (k + 1) * seg + i)
             for k in range(rangs) for i in range(seg)]
        lot.ajout(V, F, "ecorce")
        haut = V[-seg:].copy()
        haut[:, 2] -= 0.005
        Vc = np.vstack([haut, [[cx, cy, z0 + h - 0.015]]])
        lot.ajout(Vc, [(i, (i + 1) % seg, seg) for i in range(seg)], "bois", lisse=False)
        for a in rng.uniform(0, 6.3, rng.integers(4, 6)):            # racines
            r0 = 0.26
            pts = [(cx + r0 * math.cos(a) * f, cy + r0 * math.sin(a) * f, 0) for f in (0.8, 1.3, 1.8, 2.3)]
            pts = [(px, py, hauteur(px, py) + (0.06 if i == 0 else 0.015 - 0.01 * i)) for i, (px, py, _) in enumerate(pts)]
            Vt, Ft = tube(pts, [0.07, 0.05, 0.03, 0.015], 8, rugueux=0.15)
            lot.ajout(Vt, Ft, "ecorce")
        for _ in range(rng.integers(2, 4)):                           # polypores
            a, zz = rng.uniform(0, 6.3), rng.uniform(0.08, h - 0.08)
            rr = 0.24 + 0.09 * (1 - zz / h) ** 4
            inst(divers, prim("dome"),
                 mat4((cx + (rr + 0.02) * math.cos(a), cy + (rr + 0.02) * math.sin(a), z0 + zz), rz=a,
                      ech=(0.07, 0.1, 0.025)), "champignon", C=lin4("#C9B48A"))
        for _ in range(rng.integers(3, 6)):                           # champignons au pied
            a, d = rng.uniform(0, 6.3), rng.uniform(0.33, 0.45)
            champignon(divers, cx + d * math.cos(a), cy + d * math.sin(a), rng.uniform(0.05, 0.09), rng)


def construire_feuilles(lot, rng):
    n = Etat.taille
    demi = n * CELL / 2
    k = Q(int(n * n * 0.55), int(n * n * 0.25))
    X = rng.uniform(-demi + 0.1, demi - 0.1, k * 2)
    Y = rng.uniform(-demi + 0.1, demi - 0.1, k * 2)
    Wh, Wp, Wk, Wt, Fe = champs(X, Y)
    garde = (Fe < 0.15) & ~pres_du_nid(X, Y, 0.95) & (rng.random(len(X)) < 0.3 + 0.5 * (Wh + Wt))
    X, Y = X[garde][:k], Y[garde][:k]
    rangs, cols = 9, 5
    t = np.linspace(0, 1, rangs)
    u = np.linspace(-1, 1, cols)
    w = 0.42 * np.sin(np.pi * t) ** 0.85 * (1 - 0.25 * t)
    gx = u[None, :] * w[:, None]
    gy = np.repeat(t[:, None], cols, 1) - 0.5
    for px, py in zip(X, Y):
        s = rng.uniform(0.09, 0.19)
        courbe = rng.uniform(0.05, 0.3)
        gz = courbe * u[None, :] ** 2 * w[:, None] + rng.uniform(0, 0.1) * np.sin(np.pi * t)[:, None]
        V = np.stack([gx, gy, gz], -1).reshape(-1, 3)
        F = [(i * cols + j, i * cols + j + 1, (i + 1) * cols + j + 1, (i + 1) * cols + j)
             for i in range(rangs - 1) for j in range(cols - 1)]
        M = mat4((px, py, hauteur(px, py) + 0.006), rz=rng.uniform(0, 6.3),
                 rx=rng.uniform(-0.12, 0.12), ry=rng.uniform(-0.12, 0.12), ech=(s, s * 1.25, s))
        lot.ajout(xf(V, M), F, "feuille", C=PAL_FEUILLE[rng.integers(len(PAL_FEUILLE))])


def construire_brindilles(lot, rng):
    n = Etat.taille
    demi = n * CELL / 2
    faits, essais = 0, 0
    while faits < Q(55, 25) and essais < 600:
        essais += 1
        x, y = rng.uniform(-demi + 0.3, demi - 0.3, 2)
        Wh, Wp, Wk, Wt, Fe = champs(np.array([x]), np.array([y]))
        if Fe[0] > 0.1 or pres_du_nid(np.array([x]), np.array([y]), 1.0)[0]:
            continue
        L, a = rng.uniform(0.2, 0.65), rng.uniform(0, 6.3)
        dx, dy = math.cos(a), math.sin(a)
        pts, rs = [], []
        for i in range(5):
            f = i / 4
            px = x + dx * L * f + 0.04 * math.sin(f * 5 + a) * -dy
            py = y + dy * L * f + 0.04 * math.sin(f * 5 + a) * dx
            r = 0.016 * (1 - 0.6 * f) * rng.uniform(0.7, 1.2)
            pts.append((px, py, hauteur(px, py) + r * 0.6))
            rs.append(r)
        V, F = tube(pts, rs, 6)
        lot.ajout(V, F, "brindille")
        if rng.random() < 0.5:
            b = pts[2]
            a2 = a + rng.choice([-1, 1]) * rng.uniform(0.5, 0.9)
            e = (b[0] + math.cos(a2) * L * 0.35, b[1] + math.sin(a2) * L * 0.35)
            V, F = tube([b, (e[0], e[1], hauteur(*e) + 0.005)], [rs[2] * 0.7, rs[2] * 0.3], 5)
            lot.ajout(V, F, "brindille")
        faits += 1


def construire_mottes(lot, rng):
    petits = [rocher(30 + i, 1) for i in range(4)]
    for (x, y) in [(x, y) for x in range(Etat.taille) for y in range(Etat.taille)
                   if (x, y) not in Etat.carte]:
        X, Y = points_case(x, y, Q(10, 4), rng, 0.42)
        for px, py in zip(X, Y):
            s = rng.uniform(0.025, 0.07)
            inst(lot, petits[rng.integers(4)],
                 mat4((px, py, hauteur(px, py) - 0.2 * s), rz=rng.uniform(0, 6.3), ech=(s, s * 0.9, s * 0.7)),
                 "motte")


def construire_nid(lot, rng):
    """Dôme d'aiguilles de pin, comme un nid de fourmis rousses."""
    if Etat.spawn is None:
        return
    c = monde(*Etat.spawn)
    N = Q(7000, 2500)
    r = 1.12 * np.sqrt(rng.random(N * 2))
    a = rng.uniform(0, math.tau, N * 2)
    X, Y = c.x + r * np.cos(a), c.y + r * np.sin(a)
    garde = np.ones(len(X), dtype=bool)
    for (tx, ty, _p, rr) in Etat.trous_nid:
        garde &= np.hypot(X - tx, Y - ty) > rr * 1.25
    X, Y = X[garde][:N], Y[garde][:N]
    N = len(X)
    Z = hauteur_np(X, Y) + 0.004
    L = rng.uniform(0.08, 0.16, N)
    b = rng.uniform(0, math.tau, N)
    tilt = rng.uniform(-0.25, 0.35, N)
    d = np.stack([np.cos(b) * np.cos(tilt), np.sin(b) * np.cos(tilt), np.sin(tilt)], -1)
    p = np.stack([-np.sin(b), np.cos(b), np.zeros(N)], -1) * 0.0045
    A = np.stack([X, Y, Z], -1) - d * L[:, None] / 2
    B = A + d * L[:, None]
    V = np.stack([A + p, A - p, B - p, B + p], 1).reshape(-1, 3)
    F = (np.arange(N)[:, None] * 4 + np.array([0, 1, 2, 3])[None]).reshape(-1, 4)
    C = np.repeat(PAL_AIGUILLE[rng.integers(len(PAL_AIGUILLE), size=N)], 4, axis=0)
    lot.ajout(V, F, "teinte", C=C, lisse=False)
    for (tx, ty, prof, rr) in Etat.trous_nid:                     # fond noir des entrées
        inst(lot, prim("disque"), mat4((tx, ty, hauteur(tx, ty) - 0.02), ech=(rr * 0.9, rr * 0.9, 1)),
             "trou_nid")
    for _ in range(14):                                          # quelques brindilles sur le dôme
        aa, dd = rng.uniform(0, 6.3), rng.uniform(0.2, 0.85)
        px, py = c.x + dd * math.cos(aa), c.y + dd * math.sin(aa)
        b2 = rng.uniform(0, 6.3)
        q = (px + 0.18 * math.cos(b2), py + 0.18 * math.sin(b2))
        V, F = tube([(px, py, hauteur(px, py) + 0.01), (q[0], q[1], hauteur(*q) + 0.01)],
                    [0.008, 0.005], 5)
        lot.ajout(V, F, "brindille")


def choisir_arches(rng):
    def bloque(x, y):
        t = Etat.carte.get((x, y), "HORS")
        return t not in PRATICABLES and t not in ("FLAQUE", "HORS") and 0 <= x < Etat.taille \
            and 0 <= y < Etat.taille
    cand = []
    for (x, y), t in Etat.carte.items():
        if t != "CHEMIN" or not (1 <= x < Etat.taille - 1 and 1 <= y < Etat.taille - 1):
            continue
        if bloque(x, y - 1) and bloque(x, y + 1) and not bloque(x - 1, y) and not bloque(x + 1, y):
            cand.append((x, y, "vertical"))       # couloir horizontal -> arche nord-sud
        elif bloque(x - 1, y) and bloque(x + 1, y) and not bloque(x, y - 1) and not bloque(x, y + 1):
            cand.append((x, y, "horizontal"))
    rng.shuffle(cand)
    choisis = []
    for c in cand:
        if all(max(abs(c[0] - o[0]), abs(c[1] - o[1])) >= 4 for o in choisis):
            choisis.append(c)
        if len(choisis) >= Q(7, 4):
            break
    return choisis


def construire_arches(lot, rng):
    for k, (x, y, sens) in enumerate(choisir_arches(rng)):
        c = monde(x, y)
        d = Vector((0, 1, 0)) if sens == "vertical" else Vector((1, 0, 0))
        lat = Vector((-d.y, d.x, 0))
        A = c - d * 0.78 + lat * rng.uniform(-0.12, 0.12)
        B = c + d * 0.78 + lat * rng.uniform(-0.12, 0.12)
        pierre = (k % 3 == 1)
        H = rng.uniform(0.6, 0.75) if not pierre else rng.uniform(0.7, 0.85)
        pts, rs = [], []
        nb = 18
        for i in range(nb):
            t = i / (nb - 1)
            p = A.lerp(B, t)
            p += lat * 0.07 * math.sin(t * math.tau + k)
            base = hauteur(p.x, p.y) * (1 - abs(2 * t - 1) ** 0.5) + \
                (hauteur(A.x, A.y) if t < 0.5 else hauteur(B.x, B.y)) * abs(2 * t - 1) ** 0.5
            p.z = base - 0.08 + H * math.sin(math.pi * t) ** 0.75
            pts.append(tuple(p))
            pied = 1 - math.sin(math.pi * t)
            rs.append((0.15 if pierre else 0.08) * (1 + 1.1 * pied ** 2))
        if pierre:
            V, F = tube(pts, rs, 14, rugueux=0.35, graine=k * 3.1)
            lot.ajout(V, F, "pierre")
        else:
            V, F = tube(pts, rs, 10, rugueux=0.12, graine=k * 3.1)
            lot.ajout(V, F, "ecorce")
            # une racine secondaire qui se détache de l'arche
            i0 = nb // 3
            p0 = Vector(pts[i0])
            fin = p0 + lat * 0.35 + d * 0.15
            fin.z = hauteur(fin.x, fin.y) - 0.02
            mil = p0.lerp(fin, 0.5) + Vector((0, 0, 0.1))
            V, F = tube([tuple(p0), tuple(mil), tuple(fin)], [rs[i0] * 0.55, 0.025, 0.012], 8,
                        rugueux=0.1)
            lot.ajout(V, F, "ecorce")
        print(f"[fourmis] arche {'en pierre' if pierre else 'en racine'} au-dessus de la case ({x}, {y})")


def construire_eau_decor(lot, rng):
    """Nénuphars (certains en fleur) et lentilles d'eau."""
    n = Etat.taille
    pts = [(x, y) for (x, y), t in Etat.carte.items() if t == "FLAQUE"]
    gab = prim("nenuphar")
    for (x, y) in pts:
        for _ in range(rng.integers(1, 3)):
            c = monde(x, y)
            px, py = c.x + rng.uniform(-0.3, 0.3), c.y + rng.uniform(-0.3, 0.3)
            if blobs(np.array([px]), np.array([py]), Etat.masques["eau"], 1.0)[0] < 0.7:
                continue
            s = rng.uniform(0.07, 0.12)
            inst(lot, gab, mat4((px, py, NIVEAU_EAU + 0.004), rz=rng.uniform(0, 6.3), ech=(s, s, s)),
                 "nenuphar", lisse=False)
            if rng.random() < 0.35:
                for i in range(10):
                    a = i * math.tau / 10
                    p = (px + 0.025 * math.cos(a), py + 0.025 * math.sin(a), NIVEAU_EAU + 0.025)
                    inst(lot, prim("sphere_basse"), mat4(p, rz=a, ry=-0.75, ech=(0.03, 0.012, 0.004)),
                         "nenuphar_fleur")
                inst(lot, prim("sphere_basse"), mat4((px, py, NIVEAU_EAU + 0.03), ech=(0.01, 0.01, 0.008)),
                     "coeur")
    demi = n * CELL / 2
    X = rng.uniform(-demi, demi, Q(4000, 1500))
    Y = rng.uniform(-demi, demi, len(X))
    Fe = blobs(X, Y, Etat.masques["eau"], 1.0)
    sel = (Fe > 0.3) & (Fe < 0.55)
    gab = prim("disque")
    for px, py in zip(X[sel], Y[sel]):
        s = rng.uniform(0.006, 0.013)
        inst(lot, gab, mat4((px, py, NIVEAU_EAU + 0.002), ech=(s, s * 0.8, 1)), "nenuphar", lisse=False)


def construire_socle(sc, M):
    n = Etat.taille
    demi = n * CELL / 2 + 0.28
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x = demi if v.co.x > 0 else -demi
        v.co.y = demi if v.co.y > 0 else -demi
        v.co.z = -EPAISSEUR if v.co.z > 0 else -EPAISSEUR - 0.22
    bmesh.ops.bevel(bm, geom=bm.edges[:], offset=0.035, offset_type='OFFSET', segments=3,
                    profile=0.5, affect='EDGES', clamp_overlap=True)
    me = bpy.data.meshes.new("FR_socle")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(M["noyer"])
    ob = bpy.data.objects.new("Socle", me)
    sc.collection.objects.link(ob)

    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= 3.4
        v.co.y = -demi - (0.006 if v.co.y < 0 else 0.0)
        v.co.z = -EPAISSEUR - 0.11 + v.co.z * 0.14
    me = bpy.data.meshes.new("FR_plaque")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(M["laiton"])
    ob = bpy.data.objects.new("Plaque", me)
    sc.collection.objects.link(ob)

    cu = bpy.data.curves.new("FR_texte", 'FONT')
    cu.body = "FORMICA RUFA  ·  simulation Java"
    cu.size = 0.095
    cu.align_x, cu.align_y = 'CENTER', 'CENTER'
    cu.extrude = 0.002
    cu.materials.append(M["grave"])
    ob = bpy.data.objects.new("Texte", cu)
    sc.collection.objects.link(ob)
    ob.location = (0, -demi - 0.0075, -EPAISSEUR - 0.11)
    ob.rotation_euler = (math.pi / 2, 0, 0)

    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=120.0)
    for v in bm.verts:
        v.co.z = -EPAISSEUR - 0.22
    me = bpy.data.meshes.new("FR_table")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(M["table"])
    ob = bpy.data.objects.new("Table", me)
    sc.collection.objects.link(ob)


# =============================================================================
# Les petits habitants mignons du diorama
# =============================================================================
def mat_emission(nom, couleur, force):
    mat, nt, b = nouveau_mat(nom)
    entree(b, "Base Color", lin4(couleur))
    entree(b, "Emission Color", lin4(couleur))
    entree(b, "Emission Strength", force)
    return mat


def mat_verre(nom):
    mat, nt, b = nouveau_mat(nom)
    entree(b, "Base Color", (1, 1, 1, 1))
    entree(b, "Roughness", 0.0)
    entree(b, "IOR", 1.33)
    entree(b, "Transmission Weight", 1.0)
    for attr, val in (("use_raytrace_refraction", True), ("use_screen_refraction", True)):
        try:
            setattr(mat, attr, val)
        except Exception:
            pass
    mat.diffuse_color = (0.8, 0.9, 1.0, 0.3)
    return mat


def materiaux_mignons():
    return {
        "reflet": mat_emission("FR_Reflet", "#FFFFFF", 6.0),
        "joue": mat_simple("FR_Joue", "#F07890", "#F7A0B0", 0.5, 10.0, 0.0, sss=0.3),
        "rosee": mat_verre("FR_Rosee"),
        "laque_rouge": mat_simple("FR_Laque_Rouge", "#B8100A", "#E02A1A", 0.12, 8.0, 0.0, coat=1.0),
        "noir_brillant": mat_simple("FR_Noir_Brillant", "#040404", "#121212", 0.12, 9.0, 0.0, coat=1.0),
        "blanc": mat_simple("FR_Blanc", "#ECE6DA", "#FFFFFF", 0.45, 9.0, 0.05, sss=0.2),
        "escargot": mat_simple("FR_Escargot", "#B09A80", "#D4C2A6", 0.3, 12.0, 0.15, sss=0.4, coat=0.5),
        "coquille": mat_teinte("FR_Coquille", 0.3, 0.1, coat=0.6, variation=0.08),
        "aile": mat_teinte("FR_Aile", 0.45, 0.35, variation=0.06),
        "gland": mat_simple("FR_Gland", "#7A4A1E", "#A86A30", 0.25, 6.0, 0.05, coat=0.7),
        "cupule": mat_simple("FR_Cupule", "#5A4128", "#8A6A44", 0.85, 40.0, 0.9),
        "fraise": mat_simple("FR_Fraise", "#B0100C", "#E8301E", 0.18, 15.0, 0.2, coat=0.8, sss=0.3),
        "panneau": mat_simple("FR_Panneau", "#B4844E", "#D8AE78", 0.7, 4.0, 0.35, etirement=(1, 8, 1)),
    }


def amanite(lot, x, y, taille, rng, z=None):
    """Champignon rouge à pois blancs."""
    z0 = hauteur(x, y) - 0.01 if z is None else z
    h = taille * rng.uniform(0.9, 1.3)
    top = np.array([x, y, z0 + h])
    V, F = tube([(x, y, z0), (x, y, z0 + h * 0.5), tuple(top)],
                [0.2 * taille, 0.15 * taille, 0.14 * taille], 10)
    lot.ajout(V, F, "blanc")
    r = taille * rng.uniform(0.55, 0.75)
    rz = rng.uniform(0, 6.3)
    inst(lot, prim("dome"), mat4(top, rz=rz, ech=(r, r, r * 0.7)), "laque_rouge")
    inst(lot, prim("disque"), mat4(top - np.array([0, 0, r * 0.17]), ech=(r * 0.95, r * 0.95, 1)), "blanc")
    S = prim("sphere_basse")
    for i in range(rng.integers(6, 10)):
        a, phi = rng.uniform(0, 6.3), rng.uniform(0.15, 1.05)
        p = top + np.array([math.sin(phi) * math.cos(a) * r, math.sin(phi) * math.sin(a) * r,
                            math.cos(phi) * r * 0.7])
        s = r * rng.uniform(0.09, 0.15)
        inst(lot, S, mat4(p, rz=a, ry=phi, ech=(s, s, s * 0.35)), "blanc")


def coccinelle(lot, x, y, z, rz, ech=1.0):
    T = Matrix.Translation(Vector((x, y, z))) @ Matrix.Rotation(rz, 4, 'Z') @ Matrix.Diagonal((ech, ech, ech, 1))
    D, S = prim("dome"), prim("sphere_basse")
    inst(lot, D, T @ Matrix.Diagonal((0.045, 0.055, 0.036, 1)), "laque_rouge")
    for a, phi in ((0.75, 0.55), (2.4, 0.55), (-0.75, 0.55), (-2.4, 0.55), (1.57, 1.0), (-1.57, 1.0), (0, 0.0)):
        p = Vector((math.sin(phi) * math.cos(a) * 0.046, math.sin(phi) * math.sin(a) * 0.056,
                    math.cos(phi) * 0.037))
        inst(lot, S, T @ Matrix.Translation(p) @ Matrix.Diagonal((0.011, 0.011, 0.004, 1)), "noir_brillant")
    inst(lot, S, T @ Matrix.Translation((0, 0.055, 0.008)) @ Matrix.Diagonal((0.024, 0.018, 0.017, 1)),
         "noir_brillant")
    for s in (1, -1):
        inst(lot, S, T @ Matrix.Translation((s * 0.01, 0.07, 0.016)) @ Matrix.Diagonal((0.0055, 0.0055, 0.0055, 1)),
             "blanc")


def escargot(lot, x, y, rz, rng, ech=1.0):
    z0 = hauteur(x, y)
    T = mat4((x, y, z0), rz=rz, ech=(ech, ech, ech))
    V, F = tube([(0, -0.13, 0.015), (0, -0.05, 0.028), (0, 0.06, 0.032), (0, 0.15, 0.045), (0, 0.19, 0.065)],
                [0.01, 0.034, 0.036, 0.031, 0.026], 12)
    lot.ajout(xf(V, T), F, "escargot")
    S = prim("sphere")
    for s in (1, -1):
        V, F = tube([(s * 0.012, 0.18, 0.08), (s * 0.03, 0.205, 0.15)], [0.007, 0.005], 6)
        lot.ajout(xf(V, T), F, "escargot")
        inst(lot, S, T @ mat4((s * 0.031, 0.207, 0.16), ech=(0.014, 0.014, 0.014)), "blanc")
        inst(lot, S, T @ mat4((s * 0.033, 0.219, 0.164), ech=(0.0075, 0.005, 0.0085)), "noir_brillant")
        inst(lot, S, T @ mat4((s * 0.036, 0.222, 0.169), ech=(0.0025, 0.002, 0.0025)), "reflet")
    th = np.linspace(0, 3.3 * math.pi, 46)
    R = 0.078 * np.exp(-0.2 * th)
    P = np.stack([0.016 * th / th[-1], -0.02 + R * np.cos(th), 0.108 + R * np.sin(th)], -1)
    seg = 12
    V, F = tube(P, 0.062 * np.exp(-0.2 * th), seg)
    bandes = np.array([lin4("#9A5A26"), lin4("#C88A48"), lin4("#E2B47A")])
    cr = bandes[(np.arange(len(th)) // 3) % 3]
    C = np.vstack([np.repeat(cr, seg, axis=0), cr[[0]], cr[[-1]]])
    lot.ajout(xf(V, T), F, "coquille", C=C)


def aile_geo(signe, c_centre, c_bord):
    """Deux lobes (aile avant et arrière) en éventail, dégradé du centre vers le bord."""
    V, F, C = [], [], []
    for (cx, cy, rx, ry, rot) in ((0.12, 0.05, 0.13, 0.085, 0.35), (0.09, -0.06, 0.09, 0.07, -0.3)):
        base = len(V)
        V.append((signe * cx * 0.6, cy * 0.6, 0.0))
        C.append(lin4(c_centre))
        k = 18
        for i in range(k):
            a = i * math.tau / k
            ex, ey = rx * math.cos(a), ry * math.sin(a)
            x = cx + ex * math.cos(rot) - ey * math.sin(rot)
            yy = cy + ex * math.sin(rot) + ey * math.cos(rot)
            V.append((signe * x, yy, 0.004 * math.sin(3 * a)))
            C.append(lin4(c_bord))
        for i in range(k):
            F.append((base, base + 1 + i, base + 1 + (i + 1) % k))
    return np.array(V), F, np.array(C)


def creer_papillons(sc, M, rng):
    Etat.papillons = []
    couleurs = [("#8ED0F5", "#1E4E8A"), ("#FAE06A", "#9A5A10"), ("#F7A64A", "#4A2008"),
                ("#F7B6D2", "#8A2E5E"), ("#F4F2EA", "#6E6E66"), ("#B8E07A", "#3E6A1E")]
    lieux = [k for k, t in Etat.carte.items() if t in ("FLEUR", "HERBE")] or list(Etat.carte)
    nb = min(Q(6, 3), len(lieux))
    for i in range(nb):
        x, y = lieux[int(rng.integers(len(lieux)))]
        c = monde(x, y)
        cc, cb = couleurs[i % len(couleurs)]
        Vb, Fb = tube([(0, -0.06, 0), (0, 0.0, 0.004), (0, 0.05, 0.004)], [0.006, 0.011, 0.009], 8)
        lot = Lot(f"Papillon_{i}")
        lot.ajout(Vb, Fb, "noir_brillant")
        for s in (1, -1):
            Va, Fa = tube([(0, 0.05, 0.004), (s * 0.02, 0.1, 0.03)], [0.002, 0.0015], 4)
            lot.ajout(Va, Fa, "noir_brillant")
        corps = lot.objet(sc, M)
        ailes = []
        for s in (1, -1):
            la = Lot(f"Papillon_{i}_aile{'D' if s > 0 else 'G'}")
            V, F, C = aile_geo(s, cc, cb)
            la.ajout(V, F, "aile", C=C)
            o = la.objet(sc, M)
            o.parent = corps
            ailes.append(o)
        Etat.papillons.append(dict(obj=corps, ailes=ailes, centre=Vector((c.x, c.y, hauteur(c.x, c.y))),
                                   phase=float(rng.uniform(0, 50)), yaw=0.0, pos=None,
                                   ax=float(rng.uniform(0.6, 1.4)), ay=float(rng.uniform(0.6, 1.4))))


def animer_papillons(maintenant, dt):
    for b in getattr(Etat, "papillons", []):
        try:
            ob = b["obj"]
            ob.name
        except ReferenceError:
            continue
        t = maintenant * 0.55 + b["phase"]
        c = b["centre"]
        p = Vector((c.x + b["ax"] * math.sin(0.7 * t) + 0.3 * math.sin(2.3 * t),
                    c.y + b["ay"] * math.sin(1.1 * t + 1.3) + 0.25 * math.cos(1.9 * t),
                    c.z + 0.55 + 0.18 * math.sin(1.7 * t) + 0.05 * math.sin(9 * t)))
        if b["pos"] is not None:
            d = p - b["pos"]
            if d.xy.length > 1e-5:
                cible = math.atan2(d.y, d.x) - math.pi / 2
                diff = (cible - b["yaw"] + math.pi) % math.tau - math.pi
                b["yaw"] += diff * (1 - math.exp(-dt * 6))
        b["pos"] = p
        ob.location = p
        ob.rotation_euler = (0.25, 0.0, b["yaw"])
        battement = 0.2 + 1.15 * abs(math.sin(maintenant * 13 + b["phase"]))
        b["ailes"][0].rotation_euler = (0, -battement, 0)
        b["ailes"][1].rotation_euler = (0, battement, 0)


def gland(lot, x, y, rng):
    z = hauteur(x, y) + 0.026
    rz = rng.uniform(0, 6.3)
    T = mat4((x, y, z), rz=rz, rx=math.pi / 2 - 0.2)
    S, D = prim("sphere"), prim("dome")
    inst(lot, S, T @ mat4((0, 0, 0), ech=(0.028, 0.028, 0.04)), "gland")
    inst(lot, D, T @ mat4((0, 0, 0.018), ech=(0.031, 0.031, 0.024)), "cupule")
    V, F = tube([(0, 0, 0.04), (0.004, 0, 0.055)], [0.004, 0.003], 5)
    lot.ajout(xf(V, T), F, "brindille")


def fraisier(lot, x, y, rng):
    z0 = hauteur(x, y)
    S = prim("sphere_basse")
    for k in range(3):                                           # feuilles trifoliées
        a = k * math.tau / 3 + rng.uniform(-0.3, 0.3)
        tip = (x + 0.09 * math.cos(a), y + 0.09 * math.sin(a), z0 + 0.1)
        V, F = tube([(x, y, z0), (x + 0.04 * math.cos(a), y + 0.04 * math.sin(a), z0 + 0.09), tip],
                    [0.004, 0.0035, 0.003], 5)
        lot.ajout(V, F, "tige")
        for j in (-1, 0, 1):
            b = a + j * 0.7
            p = (tip[0] + 0.03 * math.cos(b), tip[1] + 0.03 * math.sin(b), tip[2] + 0.004)
            inst(lot, S, mat4(p, rz=b, ech=(0.034, 0.022, 0.003)), "tige")
    for k in range(rng.integers(1, 4)):                          # fraises pendantes
        a = rng.uniform(0, 6.3)
        p = np.array([x + 0.07 * math.cos(a), y + 0.07 * math.sin(a), z0 + 0.035])
        V, F = tube([(x, y, z0 + 0.06), (p[0], p[1], p[2] + 0.04), tuple(p + np.array([0, 0, 0.022]))],
                    [0.003, 0.0025, 0.002], 5)
        lot.ajout(V, F, "tige")
        inst(lot, prim("sphere"), mat4(p, ech=(0.022, 0.022, 0.028)), "fraise")
        for j in range(5):
            b = j * math.tau / 5
            inst(lot, S, mat4(p + np.array([0.012 * math.cos(b), 0.012 * math.sin(b), 0.025]), rz=b,
                              ech=(0.012, 0.005, 0.002)), "tige")


def panneau_nid(sc, lot, M):
    if Etat.spawn is None:
        return
    c = monde(*Etat.spawn)
    p = Vector((c.x + 0.95, c.y - 0.95, 0))
    p.z = hauteur(p.x, p.y) - 0.04
    V, F = tube([(p.x, p.y, p.z), (p.x + 0.01, p.y, p.z + 0.62)], [0.022, 0.018], 8, rugueux=0.1)
    lot.ajout(V, F, "brindille")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.bevel(bm, geom=bm.edges[:], offset=0.08, offset_type='PERCENT', segments=2, affect='EDGES')
    Vc, Fc = _depuis_bm(bm)
    rz = math.radians(-35)
    inst(lot, (Vc, Fc), mat4((p.x, p.y, p.z + 0.52), rz=rz, ech=(0.5, 0.035, 0.13)), "panneau", lisse=False)
    cu = bpy.data.curves.new("FR_panneau_texte", 'FONT')
    cu.body = "FOURMILIÈRE"
    cu.size = 0.075
    cu.align_x, cu.align_y = 'CENTER', 'CENTER'
    cu.extrude = 0.002
    cu.materials.append(M["grave"])
    ob = bpy.data.objects.new("Panneau_texte", cu)
    sc.collection.objects.link(ob)
    avant = Vector((math.sin(rz), -math.cos(rz), 0)) * 0.019
    ob.location = (p.x + avant.x, p.y + avant.y, p.z + 0.52)
    ob.rotation_euler = (math.pi / 2, 0, rz)


def construire_mignons(sc, M, rng):
    lot = Lot("Mignons")
    n = Etat.taille
    demi = n * CELL / 2

    def points_libres(k, condition):
        X = rng.uniform(-demi + 0.3, demi - 0.3, k * 6)
        Y = rng.uniform(-demi + 0.3, demi - 0.3, k * 6)
        Wh, Wp, Wk, Wt, Fe = champs(X, Y)
        ok = condition(Wh, Wp, Fe) & ~pres_du_nid(X, Y, 1.15)
        return list(zip(X[ok], Y[ok]))[:k]

    for x, y in points_libres(Q(26, 12), lambda Wh, Wp, Fe: (Wh > 0.45) & (Fe < 0.1)):
        for _ in range(rng.integers(1, 4)):                     # amanites en petits groupes
            amanite(lot, x + rng.normal(0, 0.06), y + rng.normal(0, 0.06), rng.uniform(0.05, 0.1), rng)
    for x, y in points_libres(Q(18, 8), lambda Wh, Wp, Fe: (Fe < 0.1)):
        coccinelle(lot, x, y, hauteur(x, y) + 0.004, rng.uniform(0, 6.3), rng.uniform(0.8, 1.2))
    for x, y in points_libres(Q(7, 3), lambda Wh, Wp, Fe: (Fe > 0.1) & (Fe < 0.3) | (Wh > 0.6)):
        escargot(lot, x, y, rng.uniform(0, 6.3), rng, rng.uniform(0.9, 1.25))
    for x, y in points_libres(Q(24, 10), lambda Wh, Wp, Fe: (Fe < 0.1)):
        gland(lot, x, y, rng)
    for x, y in points_libres(Q(10, 5), lambda Wh, Wp, Fe: (Wh > 0.55) & (Fe < 0.1)):
        fraisier(lot, x, y, rng)
    # gouttes de rosée
    S = prim("sphere")
    for x, y in points_libres(Q(160, 60), lambda Wh, Wp, Fe: (Fe < 0.12)):
        r = rng.uniform(0.008, 0.02)
        inst(lot, S, mat4((x, y, hauteur(x, y) + 0.6 * r), ech=(r, r, r * 0.72)), "rosee")
    panneau_nid(sc, lot, M)
    lot.objet(sc, M)
    creer_papillons(sc, M, rng)


# =============================================================================
# Fourmi rousse (Formica rufa), version « mignonne »
# =============================================================================
PIVOT_PATTES = Vector((0, 0.05, 0.06))


def _mesh_pieces(nom, pieces, M):
    lot = Lot(nom)
    for (V, F), cle in pieces:
        lot.ajout(V, F, cle)
    me = bpy.data.meshes.new("FR_" + nom)
    me.from_pydata(np.concatenate(lot.V).tolist(), [], lot.F)
    me.polygons.foreach_set("material_index", lot.Mi)
    me.polygons.foreach_set("use_smooth", lot.Ls)
    for c in lot.cles:
        me.materials.append(M[c])
    me.update()
    return me


def construire_fourmi(M):
    """Grosse tête ronde, grands yeux brillants avec reflets, joues roses,
    antennes à boule, pattes courtes et dodues."""
    S = prim("sphere")

    def sph(c, e, cle, rx=0.0):
        return ((xf(S[0], mat4(c, rx=rx, ech=e)), S[1]), cle)
    corps = [
        sph((0, 0.15, 0.092), (0.07, 0.066, 0.064), "chitine_noire"),       # tête
        sph((0, 0.055, 0.076), (0.038, 0.052, 0.038), "chitine_rousse"),    # thorax
        sph((0, 0.0, 0.078), (0.022, 0.02, 0.026), "chitine_rousse"),       # pétiole
        sph((0, -0.09, 0.085), (0.072, 0.08, 0.066), "chitine_noire", 0.2),  # abdomen
    ]
    for s in (1, -1):
        corps.append(sph((s * 0.04, 0.198, 0.106), (0.027, 0.021, 0.031), "oeil"))
        corps.append(sph((s * 0.047, 0.214, 0.122), (0.0085, 0.004, 0.0085), "reflet"))
        corps.append(sph((s * 0.034, 0.216, 0.094), (0.004, 0.002, 0.004), "reflet"))
        corps.append(sph((s * 0.054, 0.188, 0.074), (0.015, 0.006, 0.01), "joue"))
        corps.append((tube([(s * 0.022, 0.205, 0.06), (s * 0.012, 0.222, 0.056), (s * 0.004, 0.23, 0.054)],
                           [0.008, 0.006, 0.003], 6), "pattes"))
        corps.append((tube([(s * 0.024, 0.18, 0.145), (s * 0.05, 0.205, 0.205), (s * 0.085, 0.245, 0.215)],
                           [0.006, 0.0055, 0.005], 6), "pattes"))
        corps.append(sph((s * 0.088, 0.25, 0.215), (0.014, 0.014, 0.014), "chitine_rousse"))
    me_corps = _mesh_pieces("fourmi_corps", corps, M)
    graine = corps + [sph((0, 0.245, 0.06), (0.03, 0.042, 0.026), "graine")]
    me_graine = _mesh_pieces("fourmi_corps_graine", graine, M)

    def patte(s, y, ecart):
        o = np.array(PIVOT_PATTES)
        pts = [np.array(p) - o for p in ((s * 0.022, y, 0.06), (s * 0.07, y + ecart * 0.3, 0.082),
                                          (s * 0.105, y + ecart * 0.65, 0.016), (s * 0.118, y + ecart * 0.85, 0.0))]
        return [(tube([pts[0], pts[1]], [0.011, 0.01], 7), "pattes"),
                (tube([pts[1], pts[2]], [0.009, 0.007], 7), "pattes"),
                (tube([pts[2], pts[3]], [0.006, 0.006], 6), "pattes")]

    jambes = {1: (0.075, 0.10), 0: (0.05, 0.0), -1: (0.025, -0.12)}
    groupes = {"A": [], "B": []}
    for rang, (y, ecart) in jambes.items():
        for s in (1, -1):
            groupes["A" if (rang == 0) == (s < 0) else "B"] += patte(s, y, ecart)
    return (me_corps, me_graine, _mesh_pieces("fourmi_pattesA", groupes["A"], M),
            _mesh_pieces("fourmi_pattesB", groupes["B"], M))


# =============================================================================
# Construction de la scène
# =============================================================================
def construire_terrain(msg):
    t0 = time.perf_counter()
    Etat.taille = int(msg.get("taille", 20))
    Etat.carte = {(int(b[0]), int(b[1])): str(b[2]) for b in msg.get("blocs", [])}
    sp = msg.get("spawn")
    Etat.spawn = (int(sp[0]), int(sp[1])) if sp else None
    sc = bpy.data.scenes.get(Etat.scene) or bpy.data.scenes.new(Etat.scene)
    for w in bpy.context.window_manager.windows:
        w.scene = sc
    for ob in list(sc.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for me in list(bpy.data.meshes):
        if me.name.startswith("FR_") and me.users == 0:
            bpy.data.meshes.remove(me)
    Etat.fourmis = {}
    _PRIM.clear()
    rng = np.random.default_rng(12345)

    M = materiaux()
    preparer_masques()
    construire_terrain_mesh(sc, M)
    vege, divers, rochers, fleurs = Lot("Vegetation"), Lot("Details"), Lot("Rochers"), Lot("Fleurs")
    bois, sol, nid, eau = Lot("Bois"), Lot("Sol_details"), Lot("Nid"), Lot("Eau_details")
    construire_herbe(vege, divers, rng)
    construire_roseaux(vege, divers, rng)
    construire_rochers(rochers, rng)
    construire_fleurs(fleurs, rng)
    construire_souches(bois, divers, rng)
    construire_arches(bois, rng)
    construire_feuilles(sol, rng)
    construire_brindilles(sol, rng)
    construire_mottes(sol, rng)
    construire_nid(nid, rng)
    construire_eau_decor(eau, rng)
    for lot in (vege, divers, rochers, fleurs, bois, sol, nid, eau):
        lot.objet(sc, M)
    construire_socle(sc, M)
    construire_mignons(sc, M, rng)
    Etat.fourmi = construire_fourmi(M)
    regler_scene(sc)
    nb = sum(len(o.data.polygons) for o in sc.objects if o.type == 'MESH')
    print(f"[fourmis] diorama {Etat.taille}x{Etat.taille} construit en "
          f"{time.perf_counter() - t0:.1f} s ({nb} faces)")


def regler_scene(sc):
    n = Etat.taille
    for nom in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
        try:
            sc.render.engine = nom
            break
        except TypeError:
            continue
    try:
        sc.view_settings.view_transform = 'AgX'
        sc.view_settings.look = 'AgX - Punchy'
    except TypeError:
        pass
    sc.view_settings.exposure = 0.35
    ee = sc.eevee
    for attr, val in (("use_shadows", True), ("shadow_ray_count", Q(2, 1)), ("shadow_step_count", Q(6, 3)),
                      ("use_raytracing", QUALITE == "haute"), ("ray_tracing_method", 'SCREEN'),
                      ("use_fast_gi", True), ("fast_gi_method", 'GLOBAL_ILLUMINATION'),
                      ("taa_samples", Q(16, 8)), ("taa_render_samples", 64),
                      ("use_shadow_jitter_viewport", QUALITE == "haute")):
        try:
            setattr(ee, attr, val)
        except Exception:
            pass
    sc.render.resolution_x, sc.render.resolution_y = 1920, 1080

    w = bpy.data.worlds.get("FR_Ciel") or bpy.data.worlds.new("FR_Ciel")
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    lp = nt.nodes.new("ShaderNodeLightPath")
    ciel = nt.nodes.new("ShaderNodeBackground")
    ciel.inputs["Color"].default_value = lin4("#8FA9C6")
    ciel.inputs["Strength"].default_value = 0.95
    fond = nt.nodes.new("ShaderNodeBackground")
    fond.inputs["Color"].default_value = lin4("#CFE2EF")
    fond.inputs["Strength"].default_value = 1.0
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs[0])
    nt.links.new(ciel.outputs[0], mix.inputs[1])
    nt.links.new(fond.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    sc.world = w

    sun = bpy.data.lights.get("FR_Soleil") or bpy.data.lights.new("FR_Soleil", 'SUN')
    sun.energy = 5.0
    sun.angle = math.radians(3.5)
    sun.color = (1.0, 0.88, 0.72)
    so = bpy.data.objects.new("Soleil", sun)
    sc.collection.objects.link(so)
    so.rotation_euler = (math.radians(50), 0.0, math.radians(-52))
    rim = bpy.data.lights.get("FR_Contre") or bpy.data.lights.new("FR_Contre", 'AREA')
    rim.energy = 900
    rim.size = 8
    rim.color = (0.75, 0.85, 1.0)
    ro = bpy.data.objects.new("Contre_jour", rim)
    sc.collection.objects.link(ro)
    ro.location = (-n * 0.6, n * 0.8, n * 0.45)
    cible = bpy.data.objects.new("Cible", None)
    sc.collection.objects.link(cible)
    cible.location = (0, 0, -0.3)
    tr = ro.constraints.new('TRACK_TO')
    tr.target, tr.track_axis, tr.up_axis = cible, 'TRACK_NEGATIVE_Z', 'UP_Y'

    def camera(nom, lens, fstop):
        cam = bpy.data.cameras.get("FR_" + nom) or bpy.data.cameras.new("FR_" + nom)
        cam.lens, cam.clip_start, cam.clip_end = lens, 0.02, 500
        cam.dof.use_dof = True
        cam.dof.aperture_fstop = fstop
        o = bpy.data.objects.new(nom, cam)
        sc.collection.objects.link(o)
        return o

    ens = camera("Cam_Ensemble", 42, 0.35)          # faible profondeur de champ : effet maquette
    ens.location = Vector((0.72, -1.3, 0.95)).normalized() * (n * 2.05)
    tr = ens.constraints.new('TRACK_TO')
    tr.target, tr.track_axis, tr.up_axis = cible, 'TRACK_NEGATIVE_Z', 'UP_Y'
    ens.data.dof.focus_object = cible
    suivi = camera("Cam_Suivi", 35, 2.2)
    suivi.location = (0, -3, 2)
    cine = camera("Cam_Cinema", 50, 4.0)
    cine.data.dof.focus_object = cible
    Etat.regard = None
    sc.camera = {"ensemble": ens, "suivi": suivi, "cinema": cine}.get(Etat.mode, ens)

    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type != 'VIEW_3D':
                continue
            for sp in area.spaces:
                if sp.type == 'VIEW_3D':
                    sp.shading.type = 'RENDERED'
                    sp.overlay.show_overlays = False
                    sp.show_region_ui = True
                    sp.region_3d.view_perspective = 'CAMERA'
            reg = next((r for r in area.regions if r.type == 'WINDOW'), None)
            if reg is not None:
                try:
                    with bpy.context.temp_override(window=win, area=area, region=reg):
                        bpy.ops.view3d.view_center_camera()
                except Exception:
                    pass
            area.tag_redraw()


# =============================================================================
# Fourmis : points de passage + courbe lisse
# =============================================================================
def point_de_passage(i, x, y, tick):
    c = monde(x, y)
    if Etat.spawn == (x, y):
        return Vector((c.x, c.y))
    r = random.Random(i * 7919 + 13)
    voie = Vector((r.uniform(-0.16, 0.16), r.uniform(-0.16, 0.16)))
    r = random.Random(i * 104729 + tick * 31 + 7)
    alea = Vector((r.uniform(-0.07, 0.07), r.uniform(-0.07, 0.07)))
    return Vector((c.x, c.y)) + voie + alea


def creer_fourmi(i, p):
    sc = bpy.data.scenes.get(Etat.scene)
    me_c, me_g, me_a, me_b = Etat.fourmi
    corps = bpy.data.objects.new(f"Fourmi_{i:02d}", me_g if i % 3 == 1 else me_c)
    sc.collection.objects.link(corps)
    corps.scale = (ECHELLE_FOURMI,) * 3
    pattes = []
    for nom, me in (("A", me_a), ("B", me_b)):
        o = bpy.data.objects.new(f"Fourmi_{i:02d}_pattes{nom}", me)
        sc.collection.objects.link(o)
        o.parent = corps
        o.location = PIVOT_PATTES
        pattes.append(o)
    maintenant = time.perf_counter()
    corps.location = (p.x, p.y, hauteur(p.x, p.y) - 0.2)
    Etat.fourmis[i] = dict(obj=corps, pattes=pattes, hist=[(maintenant, p.copy())],
                           pos=p.copy(), yaw=random.Random(i).uniform(0, math.tau),
                           phase=0.0, nee=maintenant)


def nouvelles_positions(msg):
    if Etat.fourmi is None or bpy.data.scenes.get(Etat.scene) is None:
        return
    Etat.tick_s = max(0.05, float(msg.get("tick_ms", 350)) / 1000.0)
    tick = int(msg.get("tick", 0))
    maintenant = time.perf_counter()
    for i, x, y in msg.get("fourmis", []):
        p = point_de_passage(i, x, y, tick)
        f = Etat.fourmis.get(i)
        if f is None or f["obj"].name not in bpy.data.objects:
            creer_fourmi(i, p)
            continue
        f["hist"].append((maintenant, p))
        if len(f["hist"]) > 10:
            del f["hist"][0]


def catmull(p0, p1, p2, p3, u):
    u2, u3 = u * u, u * u * u
    return 0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u2
                  + (-p0 + 3 * p1 - 3 * p2 + p3) * u3)


def position_a(hist, t):
    if t <= hist[0][0]:
        return hist[0][1].copy()
    for k in range(len(hist) - 1):
        t0, p1 = hist[k]
        t1, p2 = hist[k + 1]
        if t < t1:
            u = (t - t0) / (t1 - t0) if t1 > t0 else 1.0
            p0 = hist[k - 1][1] if k > 0 else p1
            p3 = hist[k + 2][1] if k + 2 < len(hist) else p2
            return catmull(p0, p1, p2, p3, u)
    return hist[-1][1].copy()


def animer():
    maintenant = time.perf_counter()
    dt = min(0.1, maintenant - Etat.derniere)
    Etat.derniere = maintenant
    if Etat.noeud_eau is not None:
        try:
            Etat.noeud_eau.inputs["W"].default_value = maintenant * 0.2
        except (ReferenceError, KeyError):
            Etat.noeud_eau = None
    t_aff = maintenant - RETARD_PAS * Etat.tick_s
    for f in list(Etat.fourmis.values()):
        ob = f["obj"]
        try:
            ob.name
        except ReferenceError:
            continue
        p = position_a(f["hist"], t_aff)
        dep = p - f["pos"]
        dist = dep.length
        f["pos"] = p
        vitesse = dist / dt if dt > 0 else 0.0
        if vitesse > 0.05:
            cible = math.atan2(dep.y, dep.x) - math.pi / 2
            diff = (cible - f["yaw"] + math.pi) % math.tau - math.pi
            f["yaw"] += diff * (1 - math.exp(-dt * 14))
        f["phase"] += dist * 38.0 / ECHELLE_FOURMI
        amp = min(1.0, vitesse / 1.5)
        s = math.sin(f["phase"])
        f["pattes"][0].rotation_euler.z = 0.38 * amp * s
        f["pattes"][1].rotation_euler.z = -0.38 * amp * s
        avant = Vector((-math.sin(f["yaw"]), math.cos(f["yaw"])))
        e = 0.12 * ECHELLE_FOURMI
        h = hauteur(p.x, p.y)
        h_av = hauteur(p.x + avant.x * e, p.y + avant.y * e)
        h_ar = hauteur(p.x - avant.x * e, p.y - avant.y * e)
        tangage = math.atan2(h_av - h_ar, 2 * e)
        sortie = smooth(0.0, 0.9, maintenant - f["nee"])
        ob.location = (p.x, p.y, h - 0.16 * (1 - sortie) + 0.004 * amp * abs(s))
        ob.rotation_euler = (tangage, 0.03 * amp * s, f["yaw"])
    for f in Etat.fourmis.values():
        H = f["hist"]
        while len(H) > 4 and H[2][0] < t_aff:
            del H[0]
    animer_papillons(maintenant, dt)
    try:
        maj_camera(dt)
    except Exception:
        traceback.print_exc()


def maj_camera(dt):
    sc = bpy.data.scenes.get(Etat.scene)
    if sc is None:
        return
    n = Etat.taille
    if Etat.mode == "suivi":
        cam = sc.objects.get("Cam_Suivi")
        if cam is None or not Etat.fourmis:
            return
        f = Etat.fourmis.get(Etat.suivie) or next(iter(Etat.fourmis.values()))
        p = Vector((f["pos"].x, f["pos"].y, hauteur(f["pos"].x, f["pos"].y)))
        av = Vector((-math.sin(f["yaw"]), math.cos(f["yaw"]), 0))
        droite = Vector((av.y, -av.x, 0))
        voulu = p - av * 1.3 + droite * 0.45 + Vector((0, 0, 0.55))
        voulu.z = max(voulu.z, hauteur(voulu.x, voulu.y) + 0.35)
        k = 1 - math.exp(-dt * 2.2)
        cam.location = cam.location.lerp(voulu, k)
        regard = p + av * 0.25 + Vector((0, 0, 0.08))
        Etat.regard = regard if Etat.regard is None else Etat.regard.lerp(regard, 1 - math.exp(-dt * 5))
        v = Etat.regard - cam.location
        cam.rotation_euler = v.to_track_quat('-Z', 'Y').to_euler()
        cam.data.dof.focus_distance = v.length
    elif Etat.mode == "cinema":
        cam = sc.objects.get("Cam_Cinema")
        if cam is None:
            return
        Etat.angle += dt * 0.05
        a = Etat.angle
        cam.location = (n * 0.72 * math.cos(a), n * 0.72 * math.sin(a), n * 0.3 + 0.8 * math.sin(a * 2.3))
        v = Vector((0, 0, -0.3)) - cam.location
        cam.rotation_euler = v.to_track_quat('-Z', 'Y').to_euler()


def changer_vue(mode):
    sc = bpy.data.scenes.get(Etat.scene)
    if sc is None:
        return
    noms = {"ensemble": "Cam_Ensemble", "suivi": "Cam_Suivi", "cinema": "Cam_Cinema"}
    cam = sc.objects.get(noms.get(mode, "Cam_Ensemble"))
    if cam is None:
        return
    Etat.mode = mode
    Etat.regard = None
    if mode == "suivi" and Etat.fourmis:
        f = Etat.fourmis.get(Etat.suivie) or next(iter(Etat.fourmis.values()))
        cam.location = Vector((f["pos"].x, f["pos"].y, 2.0)) + Vector((0, -2, 0))
    sc.camera = cam
    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type == 'VIEW_3D':
                for sp in area.spaces:
                    if sp.type == 'VIEW_3D':
                        sp.region_3d.view_perspective = 'CAMERA'
                area.tag_redraw()


# =============================================================================
# Panneau « Fourmis » (barre latérale N de la vue 3D)
# =============================================================================
class FOURMIS_OT_vue(bpy.types.Operator):
    bl_idname = "fourmis.vue"
    bl_label = "Changer de vue"
    mode: bpy.props.StringProperty(default="ensemble")

    def execute(self, context):
        changer_vue(self.mode)
        return {'FINISHED'}


class FOURMIS_OT_suivante(bpy.types.Operator):
    bl_idname = "fourmis.suivante"
    bl_label = "Fourmi suivante"

    def execute(self, context):
        ids = sorted(Etat.fourmis)
        if ids:
            Etat.suivie = ids[(ids.index(Etat.suivie) + 1) % len(ids)] if Etat.suivie in ids else ids[0]
        changer_vue("suivi")
        return {'FINISHED'}


class FOURMIS_PT_panneau(bpy.types.Panel):
    bl_label = "Fourmis"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Fourmis"

    def draw(self, context):
        col = self.layout.column(align=True)
        for mode, texte, icone in (("ensemble", "Vue d'ensemble", 'VIEW_CAMERA'),
                                   ("suivi", "Suivre une fourmi", 'TRACKING'),
                                   ("cinema", "Vue cinéma", 'CAMERA_DATA')):
            op = col.operator("fourmis.vue", text=texte, icon=icone, depress=(Etat.mode == mode))
            op.mode = mode
        col.separator()
        col.operator("fourmis.suivante", text="Fourmi suivante", icon='FORWARD')
        self.layout.label(text=f"{len(Etat.fourmis)} fourmis — qualité {QUALITE}")


CLASSES = (FOURMIS_OT_vue, FOURMIS_OT_suivante, FOURMIS_PT_panneau)


def enregistrer_ui():
    for cls in CLASSES:
        ancien = getattr(bpy.types, cls.__name__, None)
        if ancien is not None:
            try:
                bpy.utils.unregister_class(ancien)
            except Exception:
                pass
        bpy.utils.register_class(cls)


# =============================================================================
# Serveur TCP non bloquant (timer Blender, pas de thread)
# =============================================================================
def traiter(msg):
    cmd = msg.get("cmd")
    if cmd == "carte":
        construire_terrain(msg)
    elif cmd == "fourmis":
        nouvelles_positions(msg)
    elif cmd == "stop":
        print("[fourmis] simulation arrêtée par Java")


class Serveur:
    def __init__(self, port=PORT):
        self.actif, self.client, self.tampon = True, None, b""
        self.srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.srv.bind((HOTE, port))
        self.srv.listen(1)
        self.srv.setblocking(False)
        bpy.app.timers.register(self.boucle, first_interval=0.1, persistent=True)
        print(f"[fourmis] en attente du programme Java sur {HOTE}:{port}")

    def boucle(self):
        if not self.actif:
            return None
        try:
            self.lire()
        except Exception:
            traceback.print_exc()
        try:
            animer()
        except Exception:
            traceback.print_exc()
        return 1 / 60

    def lire(self):
        if self.client is None:
            try:
                c, adr = self.srv.accept()
            except (BlockingIOError, InterruptedError):
                return
            c.setblocking(False)
            self.client, self.tampon = c, b""
            print(f"[fourmis] Java connecté ({adr[0]})")
        while True:
            try:
                data = self.client.recv(65536)
            except (BlockingIOError, InterruptedError):
                break
            except OSError:
                data = b""
            if not data:
                print("[fourmis] Java déconnecté")
                self.fermer_client()
                break
            self.tampon += data
        while b"\n" in self.tampon:
            ligne, self.tampon = self.tampon.split(b"\n", 1)
            if ligne.strip():
                try:
                    traiter(json.loads(ligne.decode("utf-8")))
                except Exception:
                    traceback.print_exc()

    def fermer_client(self):
        try:
            if self.client:
                self.client.close()
        except OSError:
            pass
        self.client = None

    def stop(self):
        self.actif = False
        self.fermer_client()
        try:
            self.srv.close()
        except OSError:
            pass
        print("[fourmis] serveur arrêté")


def demarrer():
    ns = bpy.app.driver_namespace
    ancien = ns.get("fourmis_serveur")
    if ancien is not None:
        ancien.stop()
    enregistrer_ui()
    try:
        ns["fourmis_serveur"] = Serveur()
    except OSError as e:
        print(f"[fourmis] impossible d'ouvrir le port {PORT} : {e}")


if __name__ == "__main__":
    demarrer()
