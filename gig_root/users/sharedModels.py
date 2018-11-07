"""
Models shared by different apps are kept in this module. Each app makes
small adapation to fit their needs.

"""
from django.db import models
import cloudinary


class Comment(models.Model):
    pass
        ##Comment belongs to band profile but also eventself.
        #cotnains a field of votes

class Video(models.Model):
    pass

class Vote(models.Model):
        #the vote can be replaced by just an integerfield
        #The vote can be done on a Artist and band profile but also on a comment
        pass

class Picture(models.Model):
    """
    Picture model represents pictures in any app. All pictures are stored in
    an extern web service called Cloudinary. Based on a `public_id` we can
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

    def __init__(self, *args, **kwargs):
        super(Picture, self).__init__(*args, **kwargs)


    def __str__(self):
        return f'self.title: {self.public_id}'

    def upload_to_cloud(self, pic):
        """
        Method will upload the given picture to cloudinaryself.
        `pic` can be different types see cloudinary documentation.
        Call to `upload_to_cloud` will change the attributes of the picture.
        However, a call to save is needed to make changes permanent.
        """
        metadata=cloudinary.uploader.upload(pic)
        self.is_removed=False
        self.title=metadata.get('file_name')
        self.height=metadata.get('height')
        self.width=metadata.get('width')
        self.public_id=metadata.get('public_id')


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

    def update_metadata(self, **metadata):
        """
        Method is mean to be called when a picture upload to cloudinary occurs
        at the browser. The `medata` holds data of the uploaded picture.
        A call to save is required to make changes permanent.
        """
        if not self.is_removed:
            #delete old reference to cloudinary
            try:
                cloudinary.api.delete_resources([self.public_id])
            except:
                pass
        self.is_removed=False
        self.title=metadata.get('file_name')
        self.height=metadata.get('height')
        self.width=metadata.get('width')
        self.public_id=metadata.get('public_id')

    def delete(self, *args, **kwargs):
        """
        Whenever the picture instance is removed. The corresponding picture in
        cloudinary is first removed.
        """
        try:
            cloudinary.api.delete_resources([self.public_id])

        except:
            pass

        super(Picture, self).delete(*args, **kwargs)

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
