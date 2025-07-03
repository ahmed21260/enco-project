import qrcode
import json
import os

def generer_qr(data, filename):
    img = qrcode.make(data)
    img.save(filename)

def generer_qrs_depuis_json(json_path, dossier_qrs, url_base):
    with open(json_path, 'r', encoding='utf-8') as f:
        machines = json.load(f)
    os.makedirs(dossier_qrs, exist_ok=True)
    for machine in machines:
        machine_id = machine.get('id') or machine.get('machine')
        if not machine_id:
            continue
        url = f"{url_base}/{machine_id}"
        filename = os.path.join(dossier_qrs, f"qr_{machine_id}.png")
        generer_qr(url, filename)
        print(f"QR généré pour {machine_id} : {filename}")

if __name__ == "__main__":
    # Exemple d'utilisation :
    # 1. Placer un fichier machines.json dans qr_manager/ au format :
    #    [ {"id": "PELLE001", "machine": "PELLE001", ... }, ... ]
    # 2. Définir l'URL de base (ex: https://docs.enco.com/machine)
    json_path = "machines.json"
    dossier_qrs = "qrs"
    url_base = "https://docs.enco.com/machine"
    generer_qrs_depuis_json(json_path, dossier_qrs, url_base) 