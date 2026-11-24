#!/bin/bash
if [ ! -f "pom.xml" ]; then
    echo "Erreur : Aucun fichier pom.xml trouvé dans le répertoire courant."
    exit 1
fi

echo "Analyse du projet Maven..."

if grep -q "javafx-maven-plugin" pom.xml; then
    echo "Projet JavaFX détecté."
    mvn clean javafx:run
else
    echo "Projet Java standard détecté."
    mvn clean compile exec:java
fi
