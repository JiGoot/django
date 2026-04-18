# import logging
# from rest_framework import permissions, status
# from rest_framework.response import Response
# from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
# from rest_framework.views import APIView
# from customer.authentication import CustomerAuthentication 
# from core.utils import formattedError

# # Define a custom ordering function for categories
# # Create a logger for this file
# logger = logging.getLogger(__name__)

# class Kitchen__ShiftList(APIView):
#     ''' [⎷] Retreive working hours of a given kitchen's Branch.'''
#     authentication_classes = [CustomerAuthentication, ]
#     permission_classes = [permissions.IsAuthenticatedOrReadOnly]
#     throttle_classes = [AnonRateThrottle, UserRateThrottle] 

#     def get(self, request, *args, **kwargs):
#         try:
#             _branch = Branch.objects.get(id=kwargs['branchID'])  
#             hours = _branch.shifts.all() 
#             return Response(ShiftSrz.default(hours), status=status.HTTP_200_OK)
#         except Exception as e:
#             logger.exception(formattedError(e))
#             return Response('Internal error occurred!', status=status.HTTP_500_INTERNAL_SERVER_ERROR) 
