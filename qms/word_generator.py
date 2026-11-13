from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from io import BytesIO
import datetime


# ── Palette noir et blanc ─────────────────────────────────────────────────────
GRIS_FOND_HEX = 'F2F2F2'
GRIS_BORD_HEX = '888888'
BLANC_HEX     = 'FFFFFF'
NOIR_HEX      = '000000'

NOIR  = RGBColor(0x00, 0x00, 0x00)
BLANC = RGBColor(0xFF, 0xFF, 0xFF)

LABEL_COLONNES = {
    'reference':     'Reference',
    'description':   'Description',
    'responsable':   'Responsable',
    'date_echeance': 'Echeance',
    'statut':        'Statut',
}


def set_cell_bg(cell, hex_color):
    tc   = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd  = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color)
    tcPr.append(shd)


def set_borders(cell, color=GRIS_BORD_HEX, size=4):
    tc        = cell._tc
    tcPr      = tc.get_or_add_tcPr()
    tcBorders = OxmlElement('w:tcBorders')
    for side in ['top', 'left', 'bottom', 'right']:
        border = OxmlElement(f'w:{side}')
        border.set(qn('w:val'), 'single')
        border.set(qn('w:sz'), str(size))
        border.set(qn('w:space'), '0')
        border.set(qn('w:color'), color)
        tcBorders.append(border)
    tcPr.append(tcBorders)


def cell_write(cell, texte, bold=False, couleur=None, taille=9,
               align=WD_ALIGN_PARAGRAPH.LEFT, italic=False):
    cell.text = ''
    para = cell.paragraphs[0]
    para.alignment = align
    para.paragraph_format.space_before = Pt(1)
    para.paragraph_format.space_after  = Pt(1)
    run = para.add_run(str(texte) if texte else '\u2014')
    run.bold           = bold
    run.italic         = italic
    run.font.name      = 'Arial'
    run.font.size      = Pt(taille)
    run.font.color.rgb = couleur or NOIR
    return run


def formater_valeur(champ, valeur):
    if valeur is None or valeur == '':
        return '\u2014'
    if champ.type_rendu == 'date':
        if isinstance(valeur, (datetime.date, datetime.datetime)):
            return valeur.strftime('%d/%m/%Y')
        try:
            return datetime.datetime.strptime(str(valeur), '%Y-%m-%d').strftime('%d/%m/%Y')
        except Exception:
            return str(valeur)
    if champ.type_rendu == 'booleen':
        if isinstance(valeur, bool):
            return 'Oui' if valeur else 'Non'
        return 'Oui' if str(valeur).lower() in ('true', 'oui', '1') else 'Non'
    return str(valeur)


def generer_word_fnc(fnc, parametres=None):
    p = parametres or {}
    nom_entreprise = p.get('nom_entreprise', 'ERP Industriel')
    reference_doc  = p.get('reference_doc', 'QMS-FNC-01')
    version_doc    = p.get('version_doc', 'V1.0')
    adresse        = p.get('adresse', '')
    logo_path      = p.get('logo_path')

    # ── Charger la structure dynamique (sections + champs actifs) ───────────
    from .models import SectionFNC
    sections_qs = SectionFNC.objects.filter(actif=True).order_by('ordre', 'nom').prefetch_related('champs')

    doc = Document()

    for sec in doc.sections:
        sec.page_width    = Cm(21)
        sec.page_height   = Cm(29.7)
        sec.top_margin    = Cm(1.5)
        sec.bottom_margin = Cm(1.5)
        sec.left_margin   = Cm(1.8)
        sec.right_margin  = Cm(1.8)

    style = doc.styles['Normal']
    style.font.name = 'Arial'
    style.font.size = Pt(9)

    # ── EN-TÊTE (toujours affiché) ────────────────────────────────────────────
    t = doc.add_table(rows=1, cols=3)
    t.columns[0].width = Cm(4)
    t.columns[1].width = Cm(10)
    t.columns[2].width = Cm(3.7)
    c0, c1, c2 = t.cell(0, 0), t.cell(0, 1), t.cell(0, 2)
    for c in [c0, c1, c2]:
        set_borders(c, NOIR_HEX)

    if logo_path:
        try:
            c0.text = ''
            para_logo = c0.paragraphs[0]
            para_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run_logo = para_logo.add_run()
            run_logo.add_picture(logo_path, width=Cm(3.2))
        except Exception:
            cell_write(c0, nom_entreprise, bold=True, couleur=NOIR, taille=10)
    else:
        cell_write(c0, nom_entreprise, bold=True, couleur=NOIR, taille=10)

    cell_write(c1, 'FICHE DE NON-CONFORMITE', bold=True, couleur=NOIR, taille=13, align=WD_ALIGN_PARAGRAPH.CENTER)
    cell_write(c2, f'{reference_doc}  {version_doc}\n{datetime.date.today().strftime("%d/%m/%Y")}',
               couleur=NOIR, taille=7, align=WD_ALIGN_PARAGRAPH.RIGHT)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # ── BANDEAU N° + STATUT (toujours affiché) ────────────────────────────────
    t2 = doc.add_table(rows=1, cols=4)
    t2.columns[0].width = Cm(6)
    t2.columns[1].width = Cm(3.5)
    t2.columns[2].width = Cm(5)
    t2.columns[3].width = Cm(3.2)
    cn, cg, cs, cd = t2.cell(0, 0), t2.cell(0, 1), t2.cell(0, 2), t2.cell(0, 3)
    for c in [cn, cg, cs, cd]:
        set_borders(c, NOIR_HEX)
    cell_write(cn, f'N  {fnc.numero}', bold=True, couleur=NOIR, taille=12)
    cell_write(cg, (fnc.gravite or '').upper(), bold=True, couleur=NOIR, taille=10, align=WD_ALIGN_PARAGRAPH.CENTER)
    cell_write(cs, fnc.statut_ref.nom if fnc.statut_ref else '',
               bold=True, couleur=NOIR, taille=9, align=WD_ALIGN_PARAGRAPH.CENTER)
    cell_write(cd, fnc.date_decouverte.strftime('%d/%m/%Y') if fnc.date_decouverte else '\u2014',
               couleur=NOIR, taille=8, align=WD_ALIGN_PARAGRAPH.RIGHT)
    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # ── HELPERS DE RENDU ──────────────────────────────────────────────────────
    def section_header(titre):
        para = doc.add_paragraph()
        para.paragraph_format.space_before = Pt(8)
        para.paragraph_format.space_after  = Pt(4)
        run = para.add_run(titre)
        run.bold           = True
        run.font.name      = 'Arial'
        run.font.size      = Pt(9)
        run.font.color.rgb = NOIR
        pPr    = para._p.get_or_add_pPr()
        pBdr   = OxmlElement('w:pBdr')
        bottom = OxmlElement('w:bottom')
        bottom.set(qn('w:val'), 'single')
        bottom.set(qn('w:sz'), '6')
        bottom.set(qn('w:space'), '1')
        bottom.set(qn('w:color'), NOIR_HEX)
        pBdr.append(bottom)
        pPr.append(pBdr)

    def ligne(label, valeur):
        t = doc.add_table(rows=1, cols=2)
        t.columns[0].width = Cm(4.5)
        t.columns[1].width = Cm(13.2)
        cl, cv = t.cell(0, 0), t.cell(0, 1)
        set_cell_bg(cl, GRIS_FOND_HEX)
        set_cell_bg(cv, BLANC_HEX)
        set_borders(cl)
        set_borders(cv)
        cell_write(cl, label, bold=True, couleur=NOIR, taille=8)
        cell_write(cv, valeur or '\u2014', taille=8)
        doc.add_paragraph().paragraph_format.space_after = Pt(2)

    def deux_cols(items):
        t = doc.add_table(rows=1, cols=4)
        t.columns[0].width = Cm(3)
        t.columns[1].width = Cm(5.7)
        t.columns[2].width = Cm(3)
        t.columns[3].width = Cm(6)
        cells = [t.cell(0, i) for i in range(4)]
        for c, bg in zip(cells, [GRIS_FOND_HEX, BLANC_HEX, GRIS_FOND_HEX, BLANC_HEX]):
            set_cell_bg(c, bg)
            set_borders(c)
        for i, (label, val) in enumerate(items):
            cell_write(cells[i*2],   label,      bold=True, couleur=NOIR, taille=8)
            cell_write(cells[i*2+1], val or '\u2014', taille=8)
        doc.add_paragraph().paragraph_format.space_after = Pt(2)

    def bloc(label, texte, lignes=3):
        t = doc.add_table(rows=2, cols=1)
        t.columns[0].width = Cm(17.7)
        cl, cv = t.cell(0, 0), t.cell(1, 0)
        set_cell_bg(cl, GRIS_FOND_HEX)
        set_cell_bg(cv, BLANC_HEX)
        set_borders(cl)
        set_borders(cv)
        cell_write(cl, label, bold=True, couleur=NOIR, taille=8)
        cell_write(cv, texte or '\u2014', taille=8)
        tr   = cv._tc.getparent()
        trPr = tr.get_or_add_trPr()
        trH  = OxmlElement('w:trHeight')
        trH.set(qn('w:val'), str(lignes * 280))
        trPr.append(trH)
        doc.add_paragraph().paragraph_format.space_after = Pt(2)

    def rendre_tableau_actions(champ):
        actions = list(fnc.actions.all()) if hasattr(fnc, 'actions') else []
        config  = champ.config_colonnes or {
            'reference': True, 'description': True, 'responsable': True,
            'date_echeance': True, 'statut': True,
        }
        colonnes_actives = [c for c in ['reference', 'description', 'responsable', 'date_echeance', 'statut']
                             if config.get(c, True)]
        if not colonnes_actives:
            return
        if not actions:
            p2 = doc.add_paragraph('Aucune action corrective enregistree')
            p2.runs[0].font.name      = 'Arial'
            p2.runs[0].font.color.rgb = NOIR
            p2.runs[0].italic         = True
            p2.runs[0].font.size      = Pt(8)
            return

        largeurs_par_colonne = {
            'reference': Cm(2.5), 'description': Cm(7.5), 'responsable': Cm(3.5),
            'date_echeance': Cm(2.5), 'statut': Cm(1.7),
        }
        widths = [largeurs_par_colonne[c] for c in colonnes_actives]

        ta = doc.add_table(rows=1 + len(actions), cols=len(colonnes_actives))
        for i, w in enumerate(widths):
            ta.columns[i].width = w
        for i, key in enumerate(colonnes_actives):
            c = ta.cell(0, i)
            set_cell_bg(c, GRIS_FOND_HEX)
            set_borders(c, NOIR_HEX)
            cell_write(c, LABEL_COLONNES[key], bold=True, couleur=NOIR, taille=8, align=WD_ALIGN_PARAGRAPH.CENTER)
        for ri, a in enumerate(actions, 1):
            bg = GRIS_FOND_HEX if ri % 2 == 0 else BLANC_HEX
            valeurs_action = {
                'reference':     a.reference or '\u2014',
                'description':   (a.description or '\u2014')[:90],
                'responsable':   a.responsable.get_full_name() if a.responsable else '\u2014',
                'date_echeance': a.date_echeance.strftime('%d/%m/%Y') if a.date_echeance else '\u2014',
                'statut':        a.statut or '\u2014',
            }
            for ci, key in enumerate(colonnes_actives):
                c = ta.cell(ri, ci)
                set_cell_bg(c, bg)
                set_borders(c)
                cell_write(c, valeurs_action[key], taille=8)
        doc.add_paragraph().paragraph_format.space_after = Pt(2)

    def rendre_bloc_signature(champ):
        signataires = champ.config_signataires or [
            {'cle': 'redacteur', 'libelle': 'Redacteur', 'actif': True},
            {'cle': 'responsable', 'libelle': 'Responsable qualite', 'actif': True},
            {'cle': 'verificateur', 'libelle': 'Verificateur', 'actif': True},
        ]
        actifs = [s for s in signataires if s.get('actif', True)]
        if not actifs:
            return
        largeur_col = Cm(17.7 / len(actifs))
        ts = doc.add_table(rows=2, cols=len(actifs))
        for i in range(len(actifs)):
            ts.columns[i].width = largeur_col
        for i, sgn in enumerate(actifs):
            ct = ts.cell(0, i)
            cb = ts.cell(1, i)
            set_cell_bg(ct, GRIS_FOND_HEX)
            set_cell_bg(cb, BLANC_HEX)
            set_borders(ct)
            set_borders(cb)
            cell_write(ct, sgn['libelle'], bold=True, couleur=NOIR, taille=8, align=WD_ALIGN_PARAGRAPH.CENTER)
            cell_write(cb, '\n\n_______________', taille=8, align=WD_ALIGN_PARAGRAPH.CENTER)
            tr   = cb._tc.getparent()
            trPr = tr.get_or_add_trPr()
            trH  = OxmlElement('w:trHeight')
            trH.set(qn('w:val'), '1400')
            trPr.append(trH)

    def rendre_champ_seul(champ, valeur):
        if champ.type_rendu == 'texte_long':
            lignes = max(2, (champ.hauteur_bloc or 15) // 5)
            bloc(champ.nom, formater_valeur(champ, valeur), lignes=lignes)
        else:
            ligne(champ.nom, formater_valeur(champ, valeur))

    def rendre_section(section_obj):
        champs = [c for c in section_obj.champs.all() if c.actif]
        champs = sorted(champs, key=lambda c: (c.ordre, c.nom))
        if not champs:
            return

        section_header(section_obj.nom.upper())

        i = 0
        while i < len(champs):
            champ = champs[i]

            if champ.type_rendu == 'tableau_actions':
                rendre_tableau_actions(champ)
                i += 1
                continue
            if champ.type_rendu == 'bloc_signature':
                rendre_bloc_signature(champ)
                i += 1
                continue

            valeur = champ.get_valeur_pour_fnc(fnc)

            if champ.largeur_rendu == 'pleine':
                rendre_champ_seul(champ, valeur)
                i += 1
                continue

            suivant = champs[i + 1] if i + 1 < len(champs) else None
            if suivant and suivant.largeur_rendu == 'moitie' and suivant.type_rendu not in ('tableau_actions', 'bloc_signature'):
                valeur_suivant = suivant.get_valeur_pour_fnc(fnc)
                deux_cols([
                    (champ.nom,   formater_valeur(champ, valeur)),
                    (suivant.nom, formater_valeur(suivant, valeur_suivant)),
                ])
                i += 2
            else:
                rendre_champ_seul(champ, valeur)
                i += 1

    # ── SECTIONS DYNAMIQUES ────────────────────────────────────────────────────
    for section_obj in sections_qs:
        rendre_section(section_obj)

    # ── PIED DE PAGE (toujours affiché) ───────────────────────────────────────
    doc.add_paragraph().paragraph_format.space_after = Pt(8)
    parties_pied = []
    if p.get('afficher_nom_pied', True):
        parties_pied.append(nom_entreprise)
    if p.get('afficher_adresse_pied', True) and adresse:
        parties_pied.append(adresse.replace('\n', ', '))
    if p.get('afficher_reference_pied', True):
        parties_pied.append(f'{reference_doc}  {version_doc}')
    if p.get('afficher_date_pied', True):
        parties_pied.append(f'Genere le {datetime.date.today().strftime("%d/%m/%Y")}')
    if p.get('afficher_confidentiel', True):
        parties_pied.append('CONFIDENTIEL')

    pied_texte = p.get('pied_de_page') or '  -  '.join(parties_pied)
    if pied_texte:
        pied = doc.add_paragraph(pied_texte)
        pied.alignment    = WD_ALIGN_PARAGRAPH.CENTER
        r = pied.runs[0]
        r.font.name      = 'Arial'
        r.font.size      = Pt(7)
        r.font.color.rgb = NOIR
        r.italic         = True

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer