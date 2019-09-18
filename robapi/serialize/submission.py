# This file is part of the Reproducible Open Benchmarks for Data Analysis
# Platform (ROB).
#
# Copyright (C) 2019 NYU.
#
# ROB is free software; you can redistribute it and/or modify it under the
# terms of the MIT License; see LICENSE file for more details.

"""Serializer for team resources."""

import robapi.serialize.hateoas as hateoas
import robapi.serialize.labels as labels


class SubmissionSerializer(object):
    """Serializer for team resources."""
    def __init__(self, urls):
        """Initialize the reference to the Url factory.

        Parameters
        ----------
        urls: robapi.service.route.UrlFactory
            Factory for resource urls
        """
        self.urls = urls

    def submission_descriptor(self, submission):
        """Get serialization for a submission descriptor. The descriptor
        contains the submission identifier, name, and the base list of HATEOAS
        references.

        Parameters
        ----------
        submission: robapi.model.submission.SubmissionHandle
            Submission handle

        Returns
        -------
        dict
        """
        return {
            labels.ID: submission.identifier,
            labels.NAME: submission.name,
            labels.LINKS: hateoas.serialize({
                hateoas.SELF: self.urls.get_submission(submission.identifier)
            })
        }

    def submission_handle(self, submission):
        """Get serialization for a submission handle.

        Parameters
        ----------
        submission: robapi.model.submission.SubmissionHandle
            Submission handle

        Returns
        -------
        dict
        """
        doc = self.submission_descriptor(submission)
        members = list()
        for u in submission.get_members():
            members.append({labels.ID: u.identifier, labels.USERNAME: u.name})
        doc[labels.MEMBERS] = members
        return doc

    def submission_listing(self, submissions):
        """Get serialization of the submission descriptor list.

        Parameters
        ----------
        submissions: list(robapi.model.submission.SubmissionHandle)
            List of submission handles

        Returns
        -------
        dict
        """
        return {
            labels.SUBMISSIONS: [
                self.submission_descriptor(s) for s in submissions
            ],
            labels.LINKS: hateoas.serialize({
                hateoas.SELF: self.urls.list_submissions()
            })
        }