import graphene
from graphene_django import DjangoObjectType
from users.schema import UserType
from graphql import GraphQLError
from django.db.models import Q

from .models import Tweet, Reaction, Comment


# Tipo de objeto para Tweet
class TweetType(DjangoObjectType):
    total_reactions = graphene.Int()
    comments = graphene.List(lambda: CommentType)
    comment_count = graphene.Int()
    reaction_count = graphene.Int()

    class Meta:
        model = Tweet

    # Resolver para contar los comentarios
    def resolve_comment_count(self, info):
        return self.comments.count()

    # Resolver para contar las reacciones
    def resolve_reaction_count(self, info):
        return self.reactions.count()

    def resolve_comments(self, info):
        return self.comments.all()
    
    def resolve_reactions(self, info):
        return self.reactions.all()


# Tipo de objeto para Reacción
class ReactionType(DjangoObjectType):
    class Meta:
        model = Reaction


# Tipo de objeto para Comentarios
class CommentType(DjangoObjectType):
    class Meta:
        model = Comment


# Consultas (Query)
class Query(graphene.ObjectType):
    tweets = graphene.List(
        TweetType,
        search=graphene.String(),
        first=graphene.Int(),
        skip=graphene.Int(),
    )
    reactions = graphene.List(ReactionType)
    comments = graphene.List(CommentType, tweet_id=graphene.Int())

    def resolve_tweets(self, info, search=None, first=None, skip=None, **kwargs):
        qs = Tweet.objects.all()
        if search:
            filter = Q(contenido__icontains=search) | Q(futbolista__icontains=search)
            qs = qs.filter(filter)
        if skip:
            qs = qs[skip:]
        if first:
            qs = qs[:first]
        return qs

    def resolve_reactions(self, info, **kwargs):
        return Reaction.objects.all()

    def resolve_comments(self, info, tweet_id=None, **kwargs):
        if tweet_id:
            return Comment.objects.filter(tweet__id=tweet_id)
        return Comment.objects.all()


# Mutaciones (Mutation)
class CreateTweet(graphene.Mutation):
    tweet = graphene.Field(TweetType)  # Cambié 'CreateTweet' por 'TweetType'

    class Arguments:
        contenido = graphene.String(required=True)
        futbolista = graphene.String(required=True)
        foto = graphene.String(required=False)

    def mutate(self, info, contenido, futbolista, foto=None):
        user = info.context.user or None

        if user.is_anonymous:
            raise GraphQLError("You must be logged in to create a tweet!")


        tweet = Tweet(
            contenido=contenido,
            futbolista=futbolista,
            posted_by=user,
            foto=foto or "",
        )
        tweet.save()

        return CreateTweet(tweet=tweet)  # Devuelvo el objeto 'tweet' creado


class CreateReaction(graphene.Mutation):
    reaction = graphene.Field(ReactionType)

    class Arguments:
        tweet_id = graphene.Int(required=True)
        reaction_type = graphene.String(required=True)

    def mutate(self, info, tweet_id, reaction_type):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError("You must be logged in to react!")

        tweet = Tweet.objects.filter(id=tweet_id).first()
        if not tweet:
            raise GraphQLError("Invalid Tweet!")
        
        # Busca si el usuario ya ha reaccionado al tweet
        existing_reaction = Reaction.objects.filter(user=user, tweet=tweet).first()

        if existing_reaction:
            # Si ya existe una reacción, la actualiza
            existing_reaction.reaction_type = reaction_type
            existing_reaction.save()
            return CreateReaction(reaction=existing_reaction)
        else:
            # Si no existe, crea una nueva reacción
            reaction = Reaction.objects.create(
                user=user,
                tweet=tweet,
                reaction_type=reaction_type
            )
        return CreateReaction(reaction=reaction)


class CreateComment(graphene.Mutation):
    comment = graphene.Field(CommentType)

    class Arguments:
        tweet_id = graphene.Int(required=True)
        text = graphene.String(required=True)

    def mutate(self, info, tweet_id, text):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError("You must be logged in to comment!")

        tweet = Tweet.objects.filter(id=tweet_id).first()
        if not tweet:
            raise GraphQLError("Invalid Tweet!")

        comment = Comment.objects.create(
            user=user,
            tweet=tweet,
            text=text
        )

        return CreateComment(comment=comment)


class DeleteComment(graphene.Mutation):
    success = graphene.Boolean()

    class Arguments:
        comment_id = graphene.Int(required=True)

    def mutate(self, info, comment_id):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError("You must be logged in to delete a comment!")

        # Verificar que el comentario exista
        comment = Comment.objects.filter(id=comment_id, user=user).first()
        if not comment:
            raise GraphQLError("Comment not found or you are not the owner of this comment!")

        # Eliminar el comentario
        comment.delete()

        return DeleteComment(success=True)


class DeleteReaction(graphene.Mutation):
    success = graphene.Boolean()

    class Arguments:
        reaction_id = graphene.Int(required=True)

    def mutate(self, info, reaction_id):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError("You must be logged in to delete a reaction!")

        # Verificar que la reacción exista
        reaction = Reaction.objects.filter(id=reaction_id, user=user).first()
        if not reaction:
            raise GraphQLError("Reaction not found or you are not the owner of this reaction!")

        # Eliminar la reacción
        reaction.delete()

        return DeleteReaction(success=True)



class DeleteTweet(graphene.Mutation):
    success = graphene.Boolean()

    class Arguments:
        tweet_id = graphene.Int(required=True)

    def mutate(self, info, tweet_id):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError("You must be logged in to delete a tweet!")

        # Verificar que el tweet exista
        tweet = Tweet.objects.filter(id=tweet_id, posted_by=user).first()
        if not tweet:
            raise GraphQLError("Tweet not found or you are not the owner of this tweet!")

        # Eliminar las reacciones y comentarios asociados al tweet
        tweet.reactions.all().delete()  # Eliminar todas las reacciones
        tweet.comments.all().delete()  # Eliminar todos los comentarios

        # Eliminar el tweet
        tweet.delete()

        return DeleteTweet(success=True)




class Mutation(graphene.ObjectType):
    create_tweet = CreateTweet.Field()
    create_reaction = CreateReaction.Field()
    create_comment = CreateComment.Field()

    # Agregar las mutaciones de eliminación
    delete_comment = DeleteComment.Field()  # Para eliminar un comentario
    delete_reaction = DeleteReaction.Field()  # Para eliminar una reacción
    delete_tweet = DeleteTweet.Field()  # Para eliminar un tweet, comentarios y reacciones asociados