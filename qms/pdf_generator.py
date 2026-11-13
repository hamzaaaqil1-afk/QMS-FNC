from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, HRFlowable, Image,
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
import datetime


# ── Palette noir et blanc ─────────────────────────────────────────────────────
NOIR       = colors.black
GRIS_FOND  = colors.HexColor('#F2F2F2')
BLANC      = colors.white
GRIS_BORD  = colors.HexColor('#888888')

LABEL_COLONNES = {
    'reference':     'Référence',
    'description':   'Description',
    'responsable':   'Responsable',
    'date_echeance': 'Échéance',
    'statut':        'Statut',
}


def formater_valeur(champ, valeur):
    """Formate une valeur selon le type_rendu du champ."""
    if valeur is None or valeur == '':
        return '—'
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


def generer_pdf_fnc(fnc, parametres=None):
    buffer = BytesIO()
    p = parametres or {}

    nom_entreprise = p.get('nom_entreprise', 'ERP Industriel')
    reference_doc  = p.get('reference_doc', 'QMS-FNC-01')
    version_doc    = p.get('version_doc', 'V1.0')
    adresse        = p.get('adresse', '')
    logo_path      = p.get('logo_path')

    # ── Charger la structure dynamique (sections + champs actifs) ───────────
    from .models import SectionFNC
    sections_qs = SectionFNC.objects.filter(actif=True).order_by('ordre', 'nom').prefetch_related('champs')

    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=15*mm, leftMargin=15*mm,
        topMargin=15*mm, bottomMargin=15*mm,
    )

    # ── Styles ────────────────────────────────────────────────────────────────
    titre_style   = ParagraphStyle('Titre',   fontSize=14, fontName='Helvetica-Bold', textColor=NOIR, alignment=TA_CENTER)
    section_style = ParagraphStyle('Section', fontSize=9,  fontName='Helvetica-Bold', textColor=NOIR, alignment=TA_LEFT)
    label_style   = ParagraphStyle('Label',   fontSize=8,  fontName='Helvetica-Bold', textColor=NOIR)
    valeur_style  = ParagraphStyle('Valeur',  fontSize=8,  fontName='Helvetica',      textColor=NOIR)
    note_style    = ParagraphStyle('Note',    fontSize=7,  fontName='Helvetica',      textColor=NOIR, alignment=TA_CENTER)

    elements = []

    # ── Helpers de rendu ──────────────────────────────────────────────────────
    def section_header(titre):
        t = Table([[Paragraph(f'  {titre}', section_style)]], colWidths=[180*mm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), GRIS_FOND),
            ('PADDING',    (0, 0), (-1, -1), 5),
            ('BOX',        (0, 0), (-1, -1), 0.75, NOIR),
        ]))
        return t

    def ligne(label, valeur, col_label=50*mm, col_val=130*mm):
        data = [[
            Paragraph(label, label_style),
            Paragraph(str(valeur) if valeur else '—', valeur_style),
        ]]
        t = Table(data, colWidths=[col_label, col_val])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), GRIS_FOND),
            ('BOX',        (0, 0), (-1, -1), 0.5, GRIS_BORD),
            ('INNERGRID',  (0, 0), (-1, -1), 0.5, GRIS_BORD),
            ('VALIGN',     (0, 0), (-1, -1), 'TOP'),
            ('PADDING',    (0, 0), (-1, -1), 5),
        ]))
        return t

    def deux_colonnes(items):
        """items = liste de (label, val) — max 2 paires."""
        row = []
        for label, val in items:
            row.append(Paragraph(label, label_style))
            row.append(Paragraph(str(val) if val else '—', valeur_style))
        data = [row]
        t = Table(data, colWidths=[35*mm, 52*mm, 35*mm, 58*mm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), GRIS_FOND),
            ('BACKGROUND', (2, 0), (2, 0), GRIS_FOND),
            ('BOX',        (0, 0), (-1, -1), 0.5, GRIS_BORD),
            ('INNERGRID',  (0, 0), (-1, -1), 0.5, GRIS_BORD),
            ('VALIGN',     (0, 0), (-1, -1), 'TOP'),
            ('PADDING',    (0, 0), (-1, -1), 5),
        ]))
        return t

    def bloc_texte(label, texte, hauteur=20*mm):
        data = [
            [Paragraph(label, label_style)],
            [Paragraph(str(texte) if texte else '—', valeur_style)],
        ]
        t = Table(data, colWidths=[180*mm], rowHeights=[6*mm, hauteur])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), GRIS_FOND),
            ('BOX',        (0, 0), (-1, -1), 0.5, GRIS_BORD),
            ('INNERGRID',  (0, 0), (-1, -1), 0.5, GRIS_BORD),
            ('VALIGN',     (0, 0), (-1, -1), 'TOP'),
            ('PADDING',    (0, 0), (-1, -1), 5),
        ]))
        return t

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
            elements.append(ligne('', 'Aucune action corrective enregistrée'))
            return

        largeurs_par_colonne = {
            'reference': 25*mm, 'description': 75*mm, 'responsable': 35*mm,
            'date_echeance': 25*mm, 'statut': 20*mm,
        }
        # Réajuste les largeurs pour occuper 180mm peu importe le nombre de colonnes actives
        total_defaut = sum(largeurs_par_colonne[c] for c in colonnes_actives)
        facteur = (180*mm) / total_defaut if total_defaut else 1
        col_widths = [largeurs_par_colonne[c] * facteur for c in colonnes_actives]

        header_row = [Paragraph(LABEL_COLONNES[c], label_style) for c in colonnes_actives]
        rows = [header_row]
        for a in actions:
            valeurs_action = {
                'reference':     a.reference or '—',
                'description':   (a.description or '—')[:80],
                'responsable':   a.responsable.get_full_name() if a.responsable else '—',
                'date_echeance': a.date_echeance.strftime('%d/%m/%Y') if a.date_echeance else '—',
                'statut':        a.statut or '—',
            }
            rows.append([Paragraph(valeurs_action[c], valeur_style) for c in colonnes_actives])

        act_table = Table(rows, colWidths=col_widths)
        act_table.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, 0), GRIS_FOND),
            ('TEXTCOLOR',     (0, 0), (-1, 0), NOIR),
            ('ROWBACKGROUNDS',(0, 1), (-1, -1), [BLANC, GRIS_FOND]),
            ('BOX',           (0, 0), (-1, -1), 0.5, GRIS_BORD),
            ('INNERGRID',     (0, 0), (-1, -1), 0.5, GRIS_BORD),
            ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
            ('PADDING',       (0, 0), (-1, -1), 4),
        ]))
        elements.append(act_table)

    def rendre_bloc_signature(champ):
        signataires = champ.config_signataires or [
            {'cle': 'redacteur', 'libelle': 'Rédacteur', 'actif': True},
            {'cle': 'responsable', 'libelle': 'Responsable qualité', 'actif': True},
            {'cle': 'verificateur', 'libelle': 'Vérificateur', 'actif': True},
        ]
        actifs = [s for s in signataires if s.get('actif', True)]
        if not actifs:
            return
        largeur_col = (180*mm) / len(actifs)
        sig_data = [[
            Paragraph(f"{s['libelle']}\n\n\n\n_______________", valeur_style) for s in actifs
        ]]
        sig_table = Table(sig_data, colWidths=[largeur_col] * len(actifs))
        sig_table.setStyle(TableStyle([
            ('BOX',            (0, 0), (-1, -1), 0.5, GRIS_BORD),
            ('INNERGRID',      (0, 0), (-1, -1), 0.5, GRIS_BORD),
            ('VALIGN',         (0, 0), (-1, -1), 'TOP'),
            ('PADDING',        (0, 0), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [GRIS_FOND]),
        ]))
        elements.append(sig_table)

    def rendre_champ_seul(champ, valeur):
        if champ.type_rendu == 'texte_long':
            hauteur = (champ.hauteur_bloc or 20) * mm
            elements.append(bloc_texte(champ.nom, valeur, hauteur=hauteur))
        else:
            elements.append(ligne(champ.nom, formater_valeur(champ, valeur)))

    def rendre_section(section):
        champs = [c for c in section.champs.all() if c.actif]
        champs = sorted(champs, key=lambda c: (c.ordre, c.nom))
        if not champs:
            return

        elements.append(section_header(section.nom.upper()))

        i = 0
        while i < len(champs):
            champ = champs[i]

            # Blocs spéciaux : toujours seuls, pleine largeur
            if champ.type_rendu == 'tableau_actions':
                rendre_tableau_actions(champ)
                i += 1
                continue
            if champ.type_rendu == 'bloc_signature':
                rendre_bloc_signature(champ)
                i += 1
                continue

            valeur = champ.get_valeur_pour_fnc(fnc)

            # Champs en pleine largeur : rendu seul
            if champ.largeur_rendu == 'pleine':
                rendre_champ_seul(champ, valeur)
                i += 1
                continue

            # Champ 'moitie' : tenter de l'apparier avec le suivant si lui aussi 'moitie'
            suivant = champs[i + 1] if i + 1 < len(champs) else None
            if suivant and suivant.largeur_rendu == 'moitie' and suivant.type_rendu not in ('tableau_actions', 'bloc_signature'):
                valeur_suivant = suivant.get_valeur_pour_fnc(fnc)
                elements.append(deux_colonnes([
                    (champ.nom,   formater_valeur(champ, valeur)),
                    (suivant.nom, formater_valeur(suivant, valeur_suivant)),
                ]))
                i += 2
            else:
                # Moitié seule (nombre impair) -> rendu en pleine largeur
                rendre_champ_seul(champ, valeur)
                i += 1

        elements.append(Spacer(1, 3*mm))

    # ── EN-TÊTE (toujours affiché) ────────────────────────────────────────────
    if logo_path:
        try:
            logo_cell = Image(logo_path, width=35*mm, height=18*mm, kind='proportional')
        except Exception:
            logo_cell = Paragraph(f'<b>{nom_entreprise}</b>', ParagraphStyle('H', fontSize=11, fontName='Helvetica-Bold', textColor=NOIR))
    else:
        logo_cell = Paragraph(f'<b>{nom_entreprise}</b>', ParagraphStyle('H', fontSize=11, fontName='Helvetica-Bold', textColor=NOIR))

    header_data = [[
        logo_cell,
        Paragraph('<b>FICHE DE NON-CONFORMITÉ</b>', titre_style),
        Paragraph(
            f'{reference_doc}<br/>Version : {version_doc}<br/>Date : {datetime.date.today().strftime("%d/%m/%Y")}',
            ParagraphStyle('Ref', fontSize=7, fontName='Helvetica', textColor=NOIR, alignment=TA_RIGHT),
        ),
    ]]
    header_table = Table(header_data, colWidths=[50*mm, 90*mm, 40*mm])
    header_table.setStyle(TableStyle([
        ('BOX',           (0, 0), (-1, -1), 1, NOIR),
        ('INNERGRID',     (0, 0), (-1, -1), 0.5, GRIS_BORD),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING',       (0, 0), (-1, -1), 6),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 4*mm))

    # ── BANDEAU N° FNC (toujours affiché) ─────────────────────────────────────
    badge_data = [[
            Paragraph(f'<b>N° {fnc.numero}</b>', ParagraphStyle('Num', fontSize=13, fontName='Helvetica-Bold', textColor=NOIR, alignment=TA_LEFT)),
            Paragraph(f'<b>{(fnc.gravite or "").upper()}</b>', ParagraphStyle('Grav', fontSize=10, fontName='Helvetica-Bold', textColor=NOIR, alignment=TA_CENTER)),
            Paragraph(f'<b>{fnc.statut_ref.nom if fnc.statut_ref else ""}</b>', ParagraphStyle('Stat', fontSize=9, fontName='Helvetica-Bold', textColor=NOIR, alignment=TA_CENTER)),
            Paragraph(fnc.date_decouverte.strftime('%d/%m/%Y') if fnc.date_decouverte else '—', ParagraphStyle('Date', fontSize=8, fontName='Helvetica', textColor=NOIR, alignment=TA_RIGHT)),
        ]]
    badge_table = Table(badge_data, colWidths=[65*mm, 35*mm, 50*mm, 30*mm])
    badge_table.setStyle(TableStyle([
        ('VALIGN',  (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('BOX',     (0, 0), (-1, -1), 1, NOIR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, GRIS_BORD),
    ]))
    elements.append(badge_table)
    elements.append(Spacer(1, 4*mm))

    # ── SECTIONS DYNAMIQUES ────────────────────────────────────────────────────
    for section in sections_qs:
        rendre_section(section)

    # ── PIED DE PAGE (toujours affiché) ───────────────────────────────────────
    parties_pied = []
    if p.get('afficher_nom_pied', True):
        parties_pied.append(nom_entreprise)
    if p.get('afficher_adresse_pied', True) and adresse:
        parties_pied.append(adresse.replace('\n', ', '))
    if p.get('afficher_reference_pied', True):
        parties_pied.append(f'{reference_doc} {version_doc}')
    if p.get('afficher_date_pied', True):
        parties_pied.append(f'Généré le {datetime.date.today().strftime("%d/%m/%Y")}')
    if p.get('afficher_confidentiel', True):
        parties_pied.append('CONFIDENTIEL')

    pied = p.get('pied_de_page') or ' — '.join(parties_pied)
    elements.append(HRFlowable(width='100%', thickness=0.5, color=NOIR))
    if pied:
        elements.append(Paragraph(pied, note_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer