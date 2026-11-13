from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Sum, Avg, Count
import datetime

from .models import (PosteCharge, Article, GammeStandard, OperationStandard,
                     NomenclatureStandard, OrdreFabrication, OperationOF,
                     LigneNomenclatureOF, PointageProduction, ArretMachine)
from .serializers import (PosteChargeSerializer, ArticleSerializer,
                          GammeStandardSerializer, OperationStandardSerializer,
                          NomenclatureStandardSerializer, OFListSerializer,
                          OFDetailSerializer, OperationOFSerializer,
                          LigneNomenclatureOFSerializer, PointageProductionSerializer,
                          ArretMachineSerializer)


class PosteChargeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class   = PosteChargeSerializer
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields   = ['type_poste', 'actif']
    search_fields      = ['code', 'libelle']

    def get_queryset(self):
        return PosteCharge.objects.all()

    @action(detail=True, methods=['get'], url_path='trs')
    def trs(self, request, pk=None):
        poste = self.get_object()
        today = datetime.date.today()
        debut_mois = today.replace(day=1)

        # Temps disponible ce mois
        jours_ouvrables = sum(1 for i in range((today - debut_mois).days + 1)
                              if (debut_mois + datetime.timedelta(days=i)).weekday() < 5)
        temps_disponible = jours_ouvrables * float(poste.capacite_heures_jour) * 60

        # Temps travaillé (opérations sur ce poste ce mois)
        ops = OperationOF.objects.filter(
            poste_charge=poste,
            date_debut_reelle__date__gte=debut_mois,
            date_debut_reelle__date__lte=today,
        )
        temps_travaille = float(ops.aggregate(s=Sum('temps_reel'))['s'] or 0)

        # Arrêts
        arrets = ArretMachine.objects.filter(
            poste_charge=poste,
            date_debut__date__gte=debut_mois,
            date_debut__date__lte=today,
        )
        temps_arret = float(arrets.aggregate(s=Sum('duree_minutes'))['s'] or 0)

        trs = round((temps_travaille / temps_disponible * 100), 1) if temps_disponible > 0 else 0

        return Response({
            'poste':            poste.libelle,
            'temps_disponible': temps_disponible,
            'temps_travaille':  temps_travaille,
            'temps_arret':      temps_arret,
            'trs':              trs,
            'nb_arrets':        arrets.count(),
        })


class ArticleViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class   = ArticleSerializer
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields   = ['type_article', 'actif']
    search_fields      = ['reference', 'designation']

    def get_queryset(self):
        return Article.objects.all()


class GammeStandardViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class   = GammeStandardSerializer
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields   = ['active', 'article']
    search_fields      = ['code', 'libelle']

    def get_queryset(self):
        return GammeStandard.objects.prefetch_related('operations').all()


class OperationStandardViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class   = OperationStandardSerializer
    filterset_fields   = ['gamme', 'poste_charge']

    def get_queryset(self):
        return OperationStandard.objects.select_related('gamme', 'poste_charge')


class NomenclatureStandardViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class   = NomenclatureStandardSerializer
    filterset_fields   = ['article', 'composant']

    def get_queryset(self):
        return NomenclatureStandard.objects.select_related('article', 'composant')


class OFViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields   = ['statut', 'priorite', 'responsable']
    search_fields      = ['reference', 'designation', 'reference_client']
    ordering           = ['-created_at']

    def get_queryset(self):
        return OrdreFabrication.objects.select_related(
            'article', 'commande_client', 'responsable', 'createur', 'gamme_source'
        ).prefetch_related('operations', 'nomenclature')

    def get_serializer_class(self):
        if self.action == 'list':
            return OFListSerializer
        return OFDetailSerializer

    def perform_create(self, serializer):
        serializer.save(createur=self.request.user)

    @action(detail=False, methods=['get'], url_path='dashboard')
    def dashboard(self, request):
        today   = datetime.date.today()
        ofs     = OrdreFabrication.objects.all()
        en_cours = ofs.filter(statut__in=['lance', 'en_cours'])

        # Calcul retards
        retards = sum(1 for of in en_cours if of.est_en_retard)

        # Taux rebut global
        total_fab   = float(ofs.aggregate(s=Sum('quantite_fabriquee'))['s'] or 0)
        total_rebut = float(ofs.aggregate(s=Sum('quantite_rebut'))['s'] or 0)
        taux_rebut  = round(total_rebut / (total_fab + total_rebut) * 100, 1) if (total_fab + total_rebut) > 0 else 0

        # Temps aujourd'hui
        pointages_today = PointageProduction.objects.filter(timestamp__date=today)

        return Response({
            'total_of':          ofs.count(),
            'en_preparation':    ofs.filter(statut='preparation').count(),
            'lances':            ofs.filter(statut='lance').count(),
            'en_cours':          ofs.filter(statut='en_cours').count(),
            'termines_mois':     ofs.filter(statut='termine', date_fin_reelle__month=today.month).count(),
            'en_retard':         retards,
            'taux_rebut_global': taux_rebut,
            'pointages_today':   pointages_today.count(),
            'priorites_urgentes':ofs.filter(statut__in=['preparation', 'lance', 'en_cours'], priorite__in=['urgente', 'critique']).count(),
        })

    @action(detail=True, methods=['post'], url_path='changer-statut')
    def changer_statut(self, request, pk=None):
        of             = self.get_object()
        nouveau_statut = request.data.get('statut')
        choix_valides  = ['preparation', 'lance', 'en_attente', 'en_cours', 'termine', 'cloture', 'annule']
        if nouveau_statut not in choix_valides:
            return Response({'erreur': 'Statut invalide'}, status=400)

        of.statut = nouveau_statut
        if nouveau_statut == 'en_cours' and not of.date_debut_reelle:
            of.date_debut_reelle = datetime.date.today()
            # Lancer la première opération
            premiere_op = of.operations.filter(statut='en_attente').order_by('ordre').first()
            if premiere_op:
                premiere_op.statut = 'en_cours'
                premiere_op.date_debut_reelle = timezone.now()
                premiere_op.save()
        if nouveau_statut == 'termine':
            of.date_fin_reelle = datetime.date.today()
            # Terminer toutes les opérations
            of.operations.filter(statut__in=['en_attente', 'en_cours']).update(statut='terminee')
        of.save()
        return Response({'message': f'OF {of.reference} → {nouveau_statut}'})

    @action(detail=True, methods=['post'], url_path='importer-gamme')
    def importer_gamme(self, request, pk=None):
        of         = self.get_object()
        gamme_id   = request.data.get('gamme_id')
        if not gamme_id:
            return Response({'erreur': 'gamme_id requis'}, status=400)
        try:
            gamme = GammeStandard.objects.get(id=gamme_id)
        except GammeStandard.DoesNotExist:
            return Response({'erreur': 'Gamme introuvable'}, status=404)

        # Supprimer opérations existantes si demandé
        if request.data.get('remplacer', False):
            of.operations.all().delete()

        for op_std in gamme.operations.all():
            OperationOF.objects.create(
                of               = of,
                numero           = op_std.numero,
                libelle          = op_std.libelle,
                poste_charge     = op_std.poste_charge,
                temps_preparation= op_std.temps_preparation,
                temps_unitaire   = op_std.temps_unitaire,
                quantite_prevue  = of.quantite_lancee,
                instructions     = op_std.instructions,
                ordre            = op_std.ordre,
            )
        of.gamme_source = gamme
        of.save()
        return Response({'message': f'{gamme.operations.count()} opérations importées'})

    @action(detail=True, methods=['post'], url_path='importer-nomenclature')
    def importer_nomenclature(self, request, pk=None):
        of          = self.get_object()
        article_id  = request.data.get('article_id') or (of.article.id if of.article else None)
        if not article_id:
            return Response({'erreur': 'article_id requis'}, status=400)

        try:
            article = Article.objects.get(id=article_id)
        except Article.DoesNotExist:
            return Response({'erreur': 'Article introuvable'}, status=404)

        if request.data.get('remplacer', False):
            of.nomenclature.all().delete()

        nomenclature = NomenclatureStandard.objects.filter(article=article)
        for ligne in nomenclature:
            LigneNomenclatureOF.objects.create(
                of                  = of,
                article             = ligne.composant,
                designation         = ligne.composant.designation,
                reference_article   = ligne.composant.reference,
                type_composant      = 'matiere' if ligne.composant.type_article == 'matiere_premiere' else 'composant',
                quantite_necessaire = float(ligne.quantite) * float(of.quantite_lancee),
                unite               = ligne.unite,
                ordre               = ligne.ordre,
            )
        return Response({'message': f'{nomenclature.count()} lignes importées'})

    @action(detail=True, methods=['get'], url_path='analyse')
    def analyse(self, request, pk=None):
        of = self.get_object()
        ops = of.operations.all()

        # Temps
        temps_prevu = sum(op.temps_total_prevu for op in ops)
        temps_reel  = sum(float(op.temps_reel or 0) for op in ops)
        ecart_temps = temps_reel - temps_prevu

        # Coûts MO
        cout_mo_prevu = sum(op.cout_prevu for op in ops)
        cout_mo_reel  = sum(op.cout_reel  for op in ops)

        # Matières
        matieres = of.nomenclature.all()
        cout_matieres_prevu = sum(
            float(l.quantite_necessaire) * float(l.article.prix_revient if l.article else 0)
            for l in matieres
        )

        # Rebuts
        total_produit = float(of.quantite_fabriquee) + float(of.quantite_rebut)
        taux_rebut = round(float(of.quantite_rebut) / total_produit * 100, 1) if total_produit > 0 else 0

        return Response({
            'reference':       of.reference,
            'designation':     of.designation,
            'quantite_lancee': float(of.quantite_lancee),
            'quantite_fabriquee': float(of.quantite_fabriquee),
            'quantite_rebut':  float(of.quantite_rebut),
            'taux_rebut':      taux_rebut,
            'avancement_pct':  of.avancement_pct,
            'temps_prevu_min': temps_prevu,
            'temps_reel_min':  temps_reel,
            'ecart_temps_min': ecart_temps,
            'ecart_pct':       round(ecart_temps / temps_prevu * 100, 1) if temps_prevu > 0 else 0,
            'cout_mo_prevu':   round(cout_mo_prevu, 2),
            'cout_mo_reel':    round(cout_mo_reel, 2),
            'cout_matieres_prevu': round(cout_matieres_prevu, 2),
            'cout_total_prevu': round(cout_mo_prevu + cout_matieres_prevu, 2),
            'cout_total_reel':  round(cout_mo_reel, 2),
            'nb_operations':   ops.count(),
            'ops_terminees':   ops.filter(statut='terminee').count(),
            'ops_en_cours':    ops.filter(statut='en_cours').count(),
        })


class OperationOFViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class   = OperationOFSerializer
    filter_backends    = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields   = ['of', 'statut', 'poste_charge', 'operateur']
    ordering           = ['ordre', 'numero']

    def get_queryset(self):
        return OperationOF.objects.select_related('of', 'poste_charge', 'operateur')

    @action(detail=True, methods=['post'], url_path='demarrer')
    def demarrer(self, request, pk=None):
        op = self.get_object()
        if op.statut not in ['en_attente', 'bloquee']:
            return Response({'erreur': 'Opération déjà en cours ou terminée'}, status=400)
        op.statut            = 'en_cours'
        op.date_debut_reelle = timezone.now()
        op.operateur         = request.user
        op.save()

        # Mettre l'OF en production si pas déjà
        of = op.of
        if of.statut in ['lance', 'en_attente']:
            of.statut = 'en_cours'
            if not of.date_debut_reelle:
                of.date_debut_reelle = datetime.date.today()
            of.save()

        PointageProduction.objects.create(
            operation     = op,
            operateur     = request.user,
            type_pointage = 'debut',
            timestamp     = timezone.now(),
        )
        return Response({'message': f'Opération {op.libelle} démarrée'})

    @action(detail=True, methods=['post'], url_path='terminer')
    def terminer(self, request, pk=None):
        op = self.get_object()
        quantite_produite = float(request.data.get('quantite_produite', 0))
        quantite_rebut    = float(request.data.get('quantite_rebut', 0))
        motif_rebut       = request.data.get('motif_rebut', '')
        temps_reel        = float(request.data.get('temps_reel', 0))

        op.statut             = 'terminee'
        op.date_fin_reelle    = timezone.now()
        op.quantite_realisee  = quantite_produite
        op.quantite_rebut     = quantite_rebut
        op.temps_reel         = temps_reel or op.temps_reel
        op.save()

        # Mettre à jour les totaux OF
        of = op.of
        of.quantite_fabriquee = float(of.quantite_fabriquee) + quantite_produite
        of.quantite_rebut     = float(of.quantite_rebut)     + quantite_rebut
        of.save()

        # Si rebut → créer FNC automatique
        if quantite_rebut > 0:
            from qms.models import NonConformite
            NonConformite.objects.create(
                libelle        = f"Rebut OF {of.reference} — Op.{op.numero} {op.libelle}",
                description    = f"Rebut détecté : {quantite_rebut} {of.unite}. Motif : {motif_rebut}",
                type_nc        = 'interne',
                origine_ecart  = 'production',
                gravite        = 'majeur' if quantite_rebut > float(of.quantite_lancee) * 0.1 else 'mineur',
                redacteur      = request.user,
            )

        PointageProduction.objects.create(
            operation       = op,
            operateur       = request.user,
            type_pointage   = 'fin',
            timestamp       = timezone.now(),
            quantite_produite = quantite_produite,
            quantite_rebut  = quantite_rebut,
            motif_rebut     = motif_rebut,
        )

        # Vérifier si toutes les ops sont terminées
        if not of.operations.exclude(statut='terminee').exists():
            of.statut          = 'termine'
            of.date_fin_reelle = datetime.date.today()
            of.save()

        return Response({'message': f'Opération {op.libelle} terminée — {quantite_produite} produit(s)'})


class LigneNomenclatureOFViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class   = LigneNomenclatureOFSerializer
    filter_backends    = [DjangoFilterBackend]
    filterset_fields   = ['of', 'disponible', 'type_composant']

    def get_queryset(self):
        return LigneNomenclatureOF.objects.select_related('of', 'article')


class PointageProductionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class   = PointageProductionSerializer
    filter_backends    = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields   = ['operation', 'operateur', 'type_pointage']
    ordering           = ['-timestamp']

    def get_queryset(self):
        return PointageProduction.objects.select_related('operation', 'operateur', 'operation__of')

    def perform_create(self, serializer):
        serializer.save(operateur=self.request.user)


class ArretMachineViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class   = ArretMachineSerializer
    filter_backends    = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields   = ['poste_charge', 'type_arret']
    ordering           = ['-date_debut']

    def get_queryset(self):
        return ArretMachine.objects.select_related('poste_charge', 'operation', 'saisi_par')

    def perform_create(self, serializer):
        arret = serializer.save(saisi_par=self.request.user)
        if arret.date_debut and arret.date_fin:
            delta = arret.date_fin - arret.date_debut
            arret.duree_minutes = int(delta.total_seconds() / 60)
            arret.save()