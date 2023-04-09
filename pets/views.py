from django.shortcuts import render
from rest_framework.views import APIView, Request, Response, status
from .models import Pet
from rest_framework.pagination import PageNumberPagination
from .serializers import PetSerializer
from groups.models import Group
from traits.models import Trait
from django.shortcuts import get_object_or_404

# Create your views here.


class PetView(APIView, PageNumberPagination):
    def post(self, request):

        pet_serializer = PetSerializer(data=request.data)
        pet_serializer.is_valid(raise_exception=True)

        group_pop = pet_serializer.validated_data.pop("group")
        traits_pop = pet_serializer.validated_data.pop("traits")

        group_filter = Group.objects.filter(
            scientific_name__iexact=group_pop["scientific_name"]
        ).first()
        # iexact: FieldLookup/Correspondência exata que não diferencia maiúsculas de minúsculas
        # first() Retorna o primeiro objeto correspondido pelo queryset ou Nonese não houver nenhum objeto correspondente

        if not group_filter:
            group_filter = Group.objects.create(**group_pop)

        created_pet = Pet.objects.create(
            **pet_serializer.validated_data, group=group_filter
        )

        for traits_pets in traits_pop:
            trait_filter = Trait.objects.filter(
                name__iexact=traits_pets["name"]
            ).first()

            if not trait_filter:
                trait_filter = Trait.objects.create(**traits_pets)

            created_pet.traits.add(trait_filter)

        pet_serializer_convert = PetSerializer(created_pet)

        return Response(pet_serializer_convert.data, status.HTTP_201_CREATED)

    def get(self, request):
        trait_find = request.query_params.get("trait", None)

        if trait_find:
            filter_trait = Trait.objects.filter(name=trait_find).get()
            result = Pet.objects.filter(traits=filter_trait).all()

            result_pagination = self.paginate_queryset(result, request, view=self)
            serializer_convert = PetSerializer(result_pagination, many=True)

            return self.get_paginated_response(serializer_convert.data)

        pets = Pet.objects.all()
        result_page = self.paginate_queryset(pets, request, view=self)
        serializer_convert2 = PetSerializer(result_page, many=True)

        return self.get_paginated_response(serializer_convert2.data)


class PetDetailView(APIView):
    def get(self, request, pet_id):
        find_pet_id = get_object_or_404(Pet, id=pet_id)
        serializer_convert = PetSerializer(find_pet_id)

        return Response(serializer_convert.data)

    def patch(self, request, pet_id):
        pet_find = get_object_or_404(Pet, id=pet_id)

        pet_serializer = PetSerializer(data=request.data, partial=True)
        pet_serializer.is_valid(raise_exception=True)

        group_pop = pet_serializer.validated_data.pop("group", None)
        trait_pop = pet_serializer.validated_data.pop("traits", None)

        if group_pop is not None:
            group_find_obj = Group.objects.get_or_create(**group_pop)[0]

            pet_find.group = group_find_obj

        if trait_pop is not None:
            for traits_pet in trait_pop:
                trait_find_obj = Trait.objects.get_or_create(**traits_pet)[0]
                pet_find.traits.add(trait_find_obj.id)

        for key, value in pet_serializer.validated_data.items():
            setattr(pet_find, key, value)

        pet_find.save()
        pet_serializer = PetSerializer(pet_find)
        return Response(pet_serializer.data)

    def delete(self, request, pet_id):
        pet_find = get_object_or_404(Pet, id=pet_id)

        pet_find.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
