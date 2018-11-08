"""
Models shared by different apps are kept in this module. Each app makes
small adapation to fit their needs.

"""
from django.db import models
import cloudinary


def str_to_int(s):
    """
    Helper method to transform strings to int
    """
    return int(float(s))

class Comment(models.Model):
    pass
        ##Comment belongs to band profile but also eventself.
        #cotnains a field of votes

class Vote(models.Model):
        #the vote can be replaced by just an integerfield
        #The vote can be done on a Artist and band profile but also on a comment
        pass

class PictureAbstract(models.Model): #TODO needs to become abstract and the other pics extend from here. Comment Video need to become mixins
    """
    PictureAbstract represents the base for pictures in any app. This abstract model provides api's to communicate
    with an extern web service called Cloudinary. Based on a `public_id` we can
    fetch the corresponding pictures.

    `title`: attribute corresponds with the file name of the picture (without the extension).
    `public_id`: the id used to store the picture in Cloudinary
    `width`: width of the picture
    `height`: height of the picture
    `is_removed`: tells whether the picture got removed from Cloudinary

    """
    MAX_LENGTH=200

    title=models.CharField(max_length=MAX_LENGTH, null=True, default=False)
    public_id=models.CharField(max_length=MAX_LENGTH, null=True, default=False)
    width = models.PositiveIntegerField(null=True, default=False)
    height = models.PositiveIntegerField(null=True, default=False)
    is_removed = models.BooleanField(null=True, default=True)

    class Meta:
        abstract = True


    def upload_to_cloud(self, pic):
        """
        Method will upload the given picture to cloudinaryself.
        `pic` can be different types see cloudinary documentation.
        Call to `upload_to_cloud` will change the attributes of the picture.
        However, a call to save is needed to make changes permanent.
        """
        metadata=cloudinary.uploader.upload(pic)
        self.is_removed=False
        self.title=metadata.get('original_filename')
        self.height= str_to_int(metadata.get('height'))
        self.width= str_to_int(metadata.get('width'))
        self.public_id= metadata.get('public_id')


    def remove_from_cloud(self, pic):
        """
        Method will remove the picture from cloudinary based on the `public_id` id.
        And will change the local attribtue of `self` picture. However, a call to
        save is needed to make changes permanent.
        """
        cloudinary.api.delete_resources([self.public_id])
        self.is_removed=True
        self.title=None
        self.height=None
        self.width=None
        self.public_id=None

    def update_metadata(self, public_id, title, width, height):
        """
        Method is mean to be called when a picture upload to cloudinary occurs
        at the browser. The `medata` holds data of the uploaded picture.
        A call to save is required to make changes permanent.
        """
        if not self.is_removed:
            #delete old reference to cloudinary
            cloudinary.api.delete_resources([self.public_id])

        self.is_removed=False
        self.title=title
        self.height= str_to_int(height)
        self.width= str_to_int(width)
        self.public_id=public_id

    def delete(self, *args, **kwargs):
        """
        Whenever the picture instance is removed. The corresponding picture in
        cloudinary is first removed.
        """
        try:
            cloudinary.api.delete_resources([self.public_id])

        except:
            pass

        super(PictureAbstract, self).delete(*args, **kwargs)

    def upload_and_save(self, pic):
        """
        Convenience method to upload `pic` to cloudinary and save `self` into DB.
        Returns `self`.
        """
        self.upload_to_cloud(pic)
        self.save()

        return self

    @staticmethod
    def delete_pics(pics=None):
        """
        Removes a collections of pics from cloudinary and the DB.
        """
        pids=[p.public_id for p in pics]
        try:
            cloudinary.api.delete_resources(pids)
        except:
            pass

        for p in pics:
            p.delete()



class VideoAbstract(models.Model):
    """
    VideoAbstract represents the base for videos in the muscians app. This abstract model provides api's to communicate
    with an extern web service called Cloudinary. Based on a `public_id` we can
    fetch the corresponding pictures.

    `title`: attribute corresponds with the file name of the Video (without the extension).
    `public_id`: the id used to store the Video in Cloudinary

    """
    MAX_LENGTH=200

    title=models.CharField(max_length=MAX_LENGTH, null=True, default=False)
    public_id=models.CharField(max_length=MAX_LENGTH, null=True, default=False)
    is_removed = models.BooleanField(null=True, default=True)

    class Meta:
        abstract = True

    def remove_from_cloud(self, pic):
        """
        Method will remove the video from cloudinary based on the `public_id` id.
        And will change the local attributes of `self` video. However, a call to
        save is needed to make changes permanent.
        """
        cloudinary.api.delete_resources([self.public_id])
        self.is_removed=True
        self.title=None
        self.public_id=None

    def update_metadata(self, public_id, title):
        """
        Method is mean to be called when a video upload to cloudinary occurs
        at the browser. A call to save is required to make changes permanent.
        """
        if not self.is_removed:
            #delete old reference to cloudinary
            cloudinary.api.delete_resources([self.public_id])

        self.is_removed=False
        self.title=title
        self.public_id=public_id

    def delete(self, *args, **kwargs):
        """
        Whenever the video instance is removed. The corresponding video in
        cloudinary is first removed.
        """
        print("Deleting")
        print(self.public_id)
        x=cloudinary.api.delete_resources([self.public_id],resource_type='video')
        print(x)
        super(VideoAbstract, self).delete(*args, **kwargs)

    @staticmethod
    def delete_videos(videos=None):
        """
        Removes a collections of videos from cloudinary and the DB.
        """
        vids=[v.public_id for v in videos]
        try:
            cloudinary.api.delete_resources(vids, resource_type='video')
        except:
            pass

        for v in videos:
            v.delete()
