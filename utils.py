# Copyright 2010 Torbjorn Bjorkman
# This file is part of cif2cell
#
# cif2cell is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# cif2cell is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with cif2cell.  If not, see <http://www.gnu.org/licenses/>.
#
#******************************************************************************************
#  Description: Definitions of basic classes for CIF2Cell.
#
#  Author:      Torbjorn Bjorkman, torbjorn.bjorkman(at)aalto.fi
#  Affiliation: COMP, Aaalto University School of Science,
#               Department of Applied Physics, Espoo, Finland
#******************************************************************************************
from __future__ import division
from math import sqrt
from elementdata import *
################################################################################################
# Miscellaneous
zero = 0.0
one = 1.0
two = 2.0
three = 3.0
four = 4.0
six = 6.0
third = 1/3
half = one/two
fourth = one/four
sixth = one/six
occepsilon = 0.000001
floatlist = [third, 2*third, half, fourth, one, zero, sqrt(2.0),sixth,5*sixth]

################################################################################################
# Exception classes
class SymmetryError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class PositionError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
    
class CellError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
    
class GeometryObjectError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
    
class SetupError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
    
################################################################################################
class GeometryObject:
    """
    Parent class for anything geometrical contains:
    compeps  : epsilon for determining when two floats are equal
    """
    def __init__(self):
        self.compeps = 0.0002

class Charge(float):
    """
    Class for representing the charge state/oxidation number of an atom (ion).
    It is just an integer, except for a modified routine for turning into a string,
    viz. a two plus ion gets the string representation '2+'
    """
    def __init__(self,i):
        float.__init__(self)
    def __str__(self):
        if abs(self-int(self)) < 0.0001:
            if int(self) == 0:
                return '0'
            elif self > 0:
                return str(abs(int(self)))+'+'
            elif self < 0:
                return str(abs(int(self)))+'-'
        else:
            if self > 0:
                return str(abs(self))+"+"
            else:
                return str(abs(self))+"-"

class Vector(list,GeometryObject):
    """
    Floating point vector describing a lattice point. Assumed to have length three.
    * Supports testing for equality using the self.compeps parameter inherited
    from the parent class GeometryObject
    * Supports testing for < using the euclidean norm (length) of the vector
    * Supports addition with another Vector, in which case the
      vectors are added component-wise.
    More methods:
    length            : returns the euclidean norm of the vector
    transform(matrix) : returns matrix*vector
    improveprecision  : identify some conspicuous numbers and improve precision
    """
    def __init__(self, vec):
        GeometryObject.__init__(self)
        list.__init__(self, vec)
    def __hash__(self):
        return hash(1.1*self[0]+1.2*self[1]+1.3*self[2])
    def __eq__(self,other):
        for i in range(3):
            if abs(self[i]-other[i]) > self.compeps:
                return False
        return True
    def length(self):
        return sqrt(self[0]**2+self[1]**2+self[2]**2)
    def __lt__(self, other):
        sl = self[0]**2+self[1]**2+self[2]**2
        ol = other[0]**2+other[1]**2+other[2]**2
        return sl < ol
    # Addition of two vectors
    def __add__(self, other):
        t = Vector([self[i]+other[i] for i in range(3)])
        return t
    # Subtraction of two vectors
    def __sub__(self, other):
        t = Vector([self[i]-other[i] for i in range(3)])
        return t
    def __neg__(self):
        return Vector([-t for t in self])
    def __str__(self):
        s = ""
        for e in self:
            if type(e) == type(1):
                s += "%2i "%e
            else:
                s+= "%19.15f "%e
        return s
    # multiplication by scalar
    def scalmult(self, a):
        for i in range(3):
            self[i] *= a
        return self
    # dot product
    def dot(self,a):
        t = 0.0
        for i in range(3):
            t += self[i]*a[i]
        return t
    # coordinate transformation
    def transform(self, matrix):
        t = Vector(mvmult3(matrix, self))
        return t
    def improveprecision(self):
        for i in range(3):
            for f in floatlist:
                if abs(self[i]-f) <= self.compeps:
                    # 0
                    self[i] = f
                    break

class LatticeVector(Vector):
    """
    Vector of length three that maps back things into the cell
    """
    def __init__(self, vec):
        Vector.__init__(self, vec)
        # Interval we wish to use for the coordinates.
        # In practice either [0,1] or [-.5, 0.5]
        self.interval = [0.0, 1.0]
        self.intocell()
        self.improveprecision()
    # Addition of two vectors, putting the result back
    # into the cell if necessary
    def __add__(self, other):
        if self.interval[0] != other.interval[0] or self.interval[1] != other.interval[1]:
            raise GeometryObjectError("LatticeVectors must have the same definition intervals to be added.")
        t = LatticeVector([self[i]+other[i] for i in range(3)])
        t.intocell()
        return t
    # Change interval
    def change_interval(self, interval):
        self.interval = interval
        t = LatticeVector([0,0,0])
        t.interval = interval
        self = self + t
    # coordinate transformation
    def transform(self, matrix):
        t = LatticeVector(mvmult3(matrix, self))
        t.intocell()
        return t
    # Put the vector components into the cell interval defined by self.interval
    def intocell(self):
        for i in range(3):
            while not (self.interval[0] <= self[i] < self.interval[1]):
                self[i] -= copysign(1,self[i])

class LatticeMatrix(GeometryObject, list):
    """
    Three by three matrix
    """
    def __init__(self,mat):
        GeometryObject.__init__(self)
        t = []
        for vec in mat:
            t.append(Vector(vec))
        list.__init__(self, t)
    # no idea whether this is a clever choice of hash function...
    def __hash__(self):
        t = 0.1*self[0][0] + 0.2*self[0][1] + 0.3*self[0][2] +\
            0.4*self[0][0] + 0.5*self[0][1] + 0.6*self[0][2] +\
            0.7*self[0][0] + 0.8*self[0][1] + 0.9*self[0][2]
        return hash(t)
    def __str__(self):
        matstr = ""
        for l in self:
            matstr += str(l)+"\n"
        return matstr
    def __eq__(self,other):
        for i in range(3):
            for j in range(3):
                if abs(self[i][j]-other[i][j]) > self.compeps:
                    return False
        return True
    # coordinate transformation
    def transform(self, matrix):
        return LatticeMatrix(mmmult3(matrix, self))
    # transpose
    def transpose(self):
        t = [[self[0][0], self[1][0], self[2][0]],
             [self[0][1], self[1][1], self[2][1]],
             [self[0][2], self[1][2], self[2][2]]]
        return LatticeMatrix(t)

class AtomSite(GeometryObject):
    """
    Class for describing an atomic site.

    Contains data:
    position  : a vector that gives the position
    species   : a dictionary with element-occupancy pairs (e.g. {Fe : 0.2, Co : 0.8})
    label     : any label
    charges   : a dictionary with the charge states (oxidation numbers) of the different species
    index     : any integer

    Functions:
        __eq__    : compare equality
        __str__   : one line with species and position info
        spcstring : species string ('Mn', 'La/Sr' ...)
        alloy     : true if there are more than one species occupying the site
        
    """
    def __init__(self,position=None,species=None,label="",charges=None,index=None):
        GeometryObject.__init__(self)
        if position != None:
            self.position = LatticeVector(position)
        else:
            self.position = None
        if species != None:
            self.species = species
        else:
            self.species = {}
        if charges != None:
            self.charges = charges
        else:
            if self.species != None:
                self.charges = {}
                for k in self.species.keys():
                    self.charges[k] = charge(0)
            else:
                self.charges = {}
        self.label = label
        ## self.charge = Charge(charge)
        self.index = index
    def __hash__(self):
        return hash(self.position)+hash(''.join(sorted(self.species.keys())))+hash(sum(self.species.values()))
    def __eq__(self,other):
        return self.position == other.position and self.species == other.species
    # Species string
    def spcstring(self):
        tmp = ""
        for k in self.species:
            tmp += k+"/"
        tmp = tmp.rstrip("/")
        return tmp
    # Is there more than one species on this site?
    def alloy(self):
        return len(self.species) > 1
    # print site data in some informative way
    def __str__(self):
        # Element symbol
        tmp = self.spcstring().ljust(8)
        # Position
        tmp += " %19.15f %19.15f %19.15f   "%(self.position[0],self.position[1],self.position[2])
        # occupancy
        for k,v in self.species.iteritems():
            tmp += str(v)+"/"
        tmp = tmp.rstrip("/")
        return tmp
    def CIradius(self,size="max",covalent=False):
        """
        Return maximal/minimal Covalent/Ionic radius of the site.
        'size' controls whether the maximal or minimal radius is returned
        'covalent' will enforce the covalent radius.
        """
        t = []
        if covalent:
            for sp in self.species.keys():
                try:
                    t.append(ElementData().CovalentRadius[sp])
                except:
                    pass
        else:
            for sp,ch in self.charges.iteritems():
                try:
                    t.append(ElementData().IonicRadius[sp+str(ch)])
                except:
                    try:
                        t.append(ElementData().CovalentRadius[sp])
                    except:
                        pass
        if size == "min":
            return min(t)
        else:
            return max(t)

class SymmetryOperation(GeometryObject):
    """
    Class describing a symmetry operation, with a rotation matrix and a translation.
    """
    def __init__(self, eqsite=None):
        GeometryObject.__init__(self)
        self.eqsite = eqsite
        if self.eqsite != None:
            self.rotation = self.rotmat()
            self.translation = LatticeVector(self.transvec())
        else:
            self.rotation = None
            self.translation = None
    def __hash__(self):
        t = 0.1*self.rotation[0][0] + 0.2*self.rotation[0][1] + 0.3*self.rotation[0][2] +\
            0.4*self.rotation[0][0] + 0.5*self.rotation[0][1] + 0.6*self.rotation[0][2] +\
            0.7*self.rotation[0][0] + 0.8*self.rotation[0][1] + 0.9*self.rotation[0][2] +\
            1.1*self.translation[0] + 1.2*self.translation[1] + 1.3*self.translation[2]
        return hash(t)
    # This way of printing was useful for outputting to CASTEP.
    def __str__(self):
        return str(self.rotation)+str(self.translation)+"\n"
    # Two symmetry operations are equal if rotation matrices and translation vector
    # differ by at most compeps
    def __eq__(self, other):
        eq = True
        for i in range(3):
            for j in range(3):
                eq = eq and abs(self.rotation[i][j] - other.rotation[i][j]) < self.compeps
            eq = eq and self.translation == other.translation
        return eq
    # Comparison between operations made by comparing lengths of translation vectors,
    # whether the rotation is diagonal and the identity is always less than anything else.
    # That way we only need to sort a list of operations to get identity first (and a reasonably
    # intuitive list order).
    def __lt__(self, other):
        if self.translation < other.translation:
            return True
        if other.translation < self.translation:
            return False
        if self.diagonal():
            # diagonal matrices "smaller"
            if not other.diagonal():
                return True
            # identity is "smallest"
            if self.rotation[0][0] == self.rotation[1][1] == self.rotation[2][2] == 1:
                return True
            return False
        else:
            return False
        return self.translation < other.translation
    # Return a rotation matrix from "x,y,z" representation of a symmetry operation
    def rotmat(self):
        mat = [[0.,0.,0.],[0.,0.,0.],[0.,0.,0.]]
        for j in range(len(self.eqsite)):
            xyz = self.eqsite[j].replace('+',' +').replace('-',' -').split()
            for i in xyz:
                if i.strip("+-") == 'x':
                    mat[0][j] = float(i.strip('x')+"1")
                elif i.strip("+-") == 'y':
                    mat[1][j] = float(i.strip('y')+"1")
                elif i.strip("+-") == 'z':
                    mat[2][j] = float(i.strip('z')+"1")            
        return LatticeMatrix(mat)
    # Return a translation vector from "x,y,z" representation of a symmetry operation
    def transvec(self):
        vec = []
        for i in range(3):
            vec.append(0.0)
        for j in range(len(self.eqsite)):
            xyz = self.eqsite[j].replace('+',' +').replace('-',' -').split()
            for i in xyz:
                if i.strip("+-xyz") != "":
                    vec[j] = eval(i)
        return LatticeVector(vec)
    # True if the operation is diagonal
    def diagonal(self):
        if abs(self.rotation[0][1]) < self.compeps and \
           abs(self.rotation[0][2]) < self.compeps and \
           abs(self.rotation[1][0]) < self.compeps and \
           abs(self.rotation[1][2]) < self.compeps and \
           abs(self.rotation[2][0]) < self.compeps and \
           abs(self.rotation[2][1]) < self.compeps:
            return True
        else:
            return False
        
################################################################################################
# Local functions
def removeerror(string):
    # Remove error estimates at the end of a number (as in 3.28(5))
    splitstr=string.split('(')
    return splitstr[0]

# Guess the "true" values of some conspicuous numbers
def improveprecision(x,eps):
    for f in floatlist:
        if abs(x-f) <= eps:                
            # 0
            return f
    # if no match found, return x
    return x

def latvectadd(a,b):
    t = []
    for i in range(3):
        t.append(a[i]+b[i])
        if abs(t[i]) >= 1-occepsilon:
            t[i] = t[i] - copysign(1,t[i])
        t[i] = improveprecision(t[i],occepsilon)
    return t

def putincell(coords,coordepsilon):
    # Put coordinates in the interval 0 <= x < 1
    for i in range(3):
        # first make the coordinate positive
        while coords[i] < 0:
            coords[i] = coords[i] + 1
        # then put it in the primitive cell
        while coords[i] > 1-coordepsilon:
            coords[i] = coords[i] - 1

# Determinant of 3x3 dimensional matrix
def det3(m):
    a = m[1][1]*m[2][2]-m[1][2]*m[2][1]
    b = m[1][2]*m[2][0]-m[1][0]*m[2][2]
    c = m[1][0]*m[2][1]-m[1][1]*m[2][0]
    return m[0][0]*a + m[0][1]*b + m[0][2]*c

# Inverse of 3x3 dimensional matrix
def minv3(m):
    di = 1/det3(m)
    w = [[(m[1][1]*m[2][2]-m[1][2]*m[2][1])*di, (m[0][2]*m[2][1]-m[0][1]*m[2][2])*di, (m[0][1]*m[1][2]-m[0][2]*m[1][1])*di],
         [(m[1][2]*m[2][0]-m[1][0]*m[2][2])*di, (m[0][0]*m[2][2]-m[0][2]*m[2][0])*di, (m[0][2]*m[1][0]-m[0][0]*m[1][2])*di],
         [(m[1][0]*m[2][1]-m[1][1]*m[2][0])*di, (m[0][1]*m[2][0]-m[0][0]*m[2][1])*di, (m[0][0]*m[1][1]-m[0][1]*m[1][0])*di]]
    return w

# matrix-vector multiplication
def mvmult3(mat,vec):
    w = [0.,0.,0.]
    for i in range(3):
        t = 0
        for j in range(3):
            t = t + mat[j][i]*vec[j]
        w[i] = t
    return w

# more efficient, but goes the other way...
## def mvmult3(mat,vec):
##     w = [0.,0.,0.]
##     t = 0
##     for i in range(3):
##         r = mat[i]
##         for j in range(3):
##             t += r[j]*vec[j]
##         w[i],t = t,0
##     return w

# matrix-matrix multiplication
def mmmult3(m1,m2):
    w = []
    for i in range(3):
        w.append([])
        for j in range(3):
            t = 0
            for k in range(3):
                t += m1[i][k]*m2[k][j]
            w[i].append(t)
    return w

def crystal_system(spacegroupnr):
    # Determine crystal system
    if 0 < spacegroupnr <= 2:
        return "triclinic"
    elif 2 < spacegroupnr <=15:
        return "monoclinic"
    elif 15 < spacegroupnr <= 74:
        return "orthorhombic"
    elif 75 < spacegroupnr <= 142:
        return "tetragonal"
    elif 142 < spacegroupnr <= 167:
        return "trigonal"
    elif 167 < spacegroupnr <= 194:
        return "hexagonal"
    elif 194 < spacegroupnr <= 230:
        return "cubic"
    else:
        return "unknown"

# Return x with the sign of y
def copysign(x, y):
    if y >= 0:
        return x
    else:
        return -x