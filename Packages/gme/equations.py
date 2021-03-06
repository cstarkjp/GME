"""
---------------------------------------------------------------------

Equation definitions and derivations using :mod:`SymPy <sympy>`.

---------------------------------------------------------------------

This module provides a derivation of GME theory using :mod:`SymPy <sympy>`
for a 2D slice of a 3D landscape along a channel transect.

Starting from a model equation for the surface-normal erosion rate in terms of
the tilt angle of the topographic surface and the distance downstream
(used to infer the flow component of the model erosion process), we derive
the fundamental function (of a co-Finsler metric space), the corresponding Hamiltonian,
and the equivalent metric tensor.
The rest of the equations are derived from these core results.



---------------------------------------------------------------------


Requires Python packages/modules:
  - :mod:`gmplib.utils`
  - :mod:`numpy`
  - :mod:`sympy`
  - :mod:`functools`

Imports symbols from the :mod:`.symbols` module

---------------------------------------------------------------------

"""


import numpy as np
import sympy as sy
from gmplib.utils import e2d
from gme.symbols import *
from sympy import Eq, S, Rational, Reals, N, \
                    pi, sqrt, numer, denom, \
                    simplify, trigsimp, factor, expand, lambdify, collect, \
                    solve, solveset, diff, Matrix, det, \
                    exp, tan, atan, sin, cos, Abs, sign, log, re, im, \
                    integrate, derive_by_array, poly
from functools import reduce

__all__ = ['Equations']


class Equations:
    r"""
    Class to solve the set of GME equations (using :mod:`SymPy <sympy>`)
    and to provide them in a form (sometimes lambdified) that can be used for
    numerical evaluation.

    Much of the derivation sequence here keeps :math:`\eta` and :math:`\mu` unspecified,
    up until the Hamiltonian is defined, but eventually values for these
    parameters need to be substituted in order to make further progress.
    In this documentation, we set :math:`\eta=3/2`, for now.

    TODO: provide solutions for both :math:`\eta=1/2` and :math:`\eta=3/2` where appropriate.

    """
    def __init__( self, parameters=None, eta=Rational(3,2), mu=Rational(3,4),
                  beta_type='sin', varphi_type='ramp', ibc_type='convex-up',
                  do_raw=False, do_idtx=False, do_geodesic=False, do_nothing=False ):
        """
        Initialize class instance.
        Define/derive all the GME equations (unless `'do_nothing'` is true) using :mod:`SymPy <sympy>`.

        Args:
            parameters (dict): dictionary of model parameter values to be used for equation substitutions (used when defining geodesic equations)
            eta (:class:`sympy.Rational <sympy.core.numbers.Rational>`): exponent in slope component of erosion model (equivalent of gradient exponent :math:`n` in SPIM)
            mu (:class:`sympy.Rational <sympy.core.numbers.Rational>`): exponent in flow component of erosion model (equivalent of area exponent :math:`m` in SPIM)
            beta_type (str): choice of slope component of erosion model (`'sin'` or `'tan'`)
            varphi_type (str): choice of flow component of erosion model (`'ramp'` or `'ramp-flat'`)
            ibc_type (str): choice of initial boundary shape (`'convex-up'` or `'concave-up'`, i.e., concave vs convex in mathematical parlance)
            do_raw (bool): suppress substitution of :math:`eta` value when defining `xi_varphi_beta_eqn`?
            do_idtx (bool): generate indicatrix and figuratrix equations?
            do_geodesic (bool): generate geodesic equations?
            do_nothing (bool): just create the class instance and set its data, but don't run any of the equation definition methods

        Attributes:
            GME equations (:class:`sympy.Eq <sympy.core.relational.Equality>` etc):
                See below
        """

        self.eta = eta
        self.mu = mu
        self.do_raw = do_raw
        self.ibc_type = ibc_type
        self.beta_type = beta_type
        self.varphi_type = varphi_type
        if do_nothing: return

        self.define_p_eqns()
        self.define_r_eqns()
        self.define_xi_eqns()
        self.define_xi_model_eqn()
        self.define_xi_related_eqns()
        self.define_varphi_model_eqn()
        self.define_varphi_related_eqns()
        self.define_Fstar_eqns()
        self.define_H_eqns()
        self.define_rdot_eqns()
        self.define_pdot_eqns()
        self.define_Hamiltons_eqns()
        self.define_tanalpha_eqns()
        self.define_tanbeta_eqns()
        self.define_g_eqns()
        if do_idtx: self.define_idtx_fgtx_eqns()
        if do_geodesic:
            self.prep_geodesic_eqns(parameters if not do_raw else None)
            self.define_geodesic_eqns(parameters if not do_raw else None)
        self.define_px_poly_eqn()
        self.prep_ibc_eqns()
        self.define_ibc_eqns()
        self.set_ibc_eqns()


    def define_p_eqns(self):
        r"""
        Define normal slowness :math:`p` and derive related equations

        Attributes:
            p_covec_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`\mathbf{\widetilde{p}} := [p_x, p_z]`
            px_p_beta_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`p_x = p \sin\beta`
            pz_p_beta_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`p_z = p \cos\beta`
            p_norm_pxpz_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`p = \sqrt{p_x^2+p_z^2}`
            tanbeta_pxpz_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`\tan\beta = -\dfrac{p_x}{p_z}`
            sinbeta_pxpz_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`\sin\beta = \dfrac{p_x}{\sqrt{p_x^2+p_z^2}}`
            cosbeta_pxpz_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`\cos\beta = \dfrac{-p_z}{\sqrt{p_x^2+p_z^2}}`
            pz_px_tanbeta_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`p_z = -\dfrac{p_x}{\tan\beta}`
            px_pz_tanbeta_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`p_x = -{p_z}{\tan\beta}`
            p_pz_cosbeta_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`p = -\dfrac{p_z}{\cos\beta}`
        """
        self.p_covec_eqn = Eq(pcovec,Matrix([px,pz]).T)
        self.px_p_beta_eqn = Eq( px, p*sin(beta) )
        self.pz_p_beta_eqn = Eq( pz, -p*cos(beta) )
        self.p_norm_pxpz_eqn = Eq( trigsimp(sqrt(self.px_p_beta_eqn.rhs**2 + self.pz_p_beta_eqn.rhs**2)),
                                   (sqrt(self.px_p_beta_eqn.lhs**2 + self.pz_p_beta_eqn.lhs**2)) )
        self.tanbeta_pxpz_eqn = Eq( simplify(-self.px_p_beta_eqn.rhs/self.pz_p_beta_eqn.rhs),
                                             -self.px_p_beta_eqn.lhs/self.pz_p_beta_eqn.lhs )
        self.sinbeta_pxpz_eqn = sy.Eq(sin(beta),
                    solve(self.px_p_beta_eqn,sin(beta))[0].subs(e2d(self.p_norm_pxpz_eqn)))
        self.cosbeta_pxpz_eqn = sy.Eq(cos(beta),
                    solve(self.pz_p_beta_eqn,cos(beta))[0].subs(e2d(self.p_norm_pxpz_eqn)))
        self.pz_px_tanbeta_eqn = Eq(pz, solve(self.tanbeta_pxpz_eqn,pz)[0])
        self.px_pz_tanbeta_eqn = Eq(px, solve(self.tanbeta_pxpz_eqn,px)[0])
        self.p_pz_cosbeta_eqn = Eq(p, solve(self.pz_p_beta_eqn,p)[0])


    def define_r_eqns(self):
        r"""
        Define equations for ray position :math:`\vec{r}`

        Attributes:
            rx_r_alpha_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`r^x = r\cos\alpha`
            rz_r_alpha_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`r^z = r\sin\alpha`
        """
        self.rx_r_alpha_eqn = Eq( rx, r*cos(alpha) )
        self.rz_r_alpha_eqn = Eq( rz, r*sin(alpha) )


    def define_xi_eqns(self):
        r"""
        Define equations for surface erosion speed :math:`\xi` and its vertical behavior

        Attributes:
            xi_p_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`\xi^{\perp} := \dfrac{1}{p}`
            xiv_pz_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`\xi^{\downarrow} := -\dfrac{1}{p_z}`
            p_xi_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`{p} = \dfrac{1}{\xi^{\perp}}`
            pz_xiv_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`{p_z} = -\dfrac{1}{\xi^{\downarrow}}`
        """
        self.xi_p_eqn = Eq( xi, 1/p )
        self.xiv_pz_eqn = (Eq( xiv, -1/pz ))
        self.p_xi_eqn = Eq(p, solve(self.xi_p_eqn,p)[0])
        self.pz_xiv_eqn = Eq(pz, solve(self.xiv_pz_eqn,pz)[0])


    def define_xi_model_eqn(self):
        r"""
        Define the form of the surface erosion model,
        giving the speed of surface motion in its normal direction :math:`\xi^{\perp}``.
        For now, the model must have a separable dependence on
        position :math:`\mathbf{r}` and surface tilt :math:`\beta`.
        The former sets the 'flow' dependence of the erosion model, and is given by
        the function :math:`\varphi(\mathbf{})`, which must be specified at some point.
        The latter is specified in `self.beta_type` and may be `sin` or `tan`;
        it is given a power exponent :math:`\eta` which must take a rational value.

        Attributes:
            xi_varphi_beta_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`\xi^{\perp} = \varphi(\mathbf{r}) \, \left| \sin\beta \right|^\eta`
        """
        if self.beta_type=='sin':
            xi_model = varphi_r*abs(sin(beta))**eta
        else:
            xi_model = varphi_r*abs(tan(beta))**eta
        if self.do_raw:
            self.xi_varphi_beta_eqn = Eq(xi, xi_model)
        else:
            self.xi_varphi_beta_eqn = Eq(xi, xi_model.subs({eta: self.eta}))


    def define_xi_related_eqns(self):
        r"""
        Define equations related to surface erosion speed :math:`\xi` and its vertical behavior.
        The derivations below are for an erosion model with
        :math:`\left|\tan\beta\right|^\eta`, :math:`\eta=3/2`.

        Attributes:
            xiv_varphi_pxpz_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`\xi^{\downarrow} = - \dfrac{p_{x}^{\eta} \left(p_{x}^{2} + p_{z}^{2}\right)^{\tfrac{1}{2} - \tfrac{\eta}{2}} \varphi{\left(\mathbf{r} \right)}}{p_{z}}`
            px_xiv_varphi_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`\left(\xi^{\downarrow}\right)^{2}`
                :math:`\left(p_{x}^{2} p_{x}^{2 \eta} \left(p_{x}^{2} \
                + \frac{1}{\left(\xi^{\downarrow}\right)^{2}}\right)^{- \eta} \varphi^{2}{\left(\mathbf{r} \right)} - 1 \
                + \dfrac{p_{x}^{2 \eta} \left(p_{x}^{2} \
                + \frac{1}{\left(\xi^{\downarrow}\right)^{2}}\right)^{- \eta} \varphi^{2}{\left(\mathbf{r} \right)}}{\left(\xi^{\downarrow}\right)^{2}}\right)`
                :math:`\times\,\,\,\left(p_{x}^{2} p_{x}^{2 \eta} \left(p_{x}^{2} \
                + \frac{1}{\left(\xi^{\downarrow}\right)^{2}}\right)^{- \eta} \varphi^{2}{\left(\mathbf{r} \right)} + 1 \
                + \dfrac{p_{x}^{2 \eta} \left(p_{x}^{2} \
                + \frac{1}{\left(\xi^{\downarrow}\right)^{2}}\right)^{- \eta} \varphi^{2}{\left(\mathbf{r} \right)}}{\left(\xi^{\downarrow}\right)^{2}}\right) = 0`
            eta_dbldenom   (:class:`sympy.Int <sympy.core.numbers.Integer>`) :
                a convenience variable, recording double the denominator of :math:`\eta`, which must itself be a rational number
        """
        eta_dbldenom = 2*denom(self.eta)
        self.xiv_varphi_pxpz_eqn = simplify( Eq( xiv, (self.xi_varphi_beta_eqn.rhs/cos(beta))
                                                .subs(e2d(self.tanbeta_pxpz_eqn))
                                                .subs(e2d(self.cosbeta_pxpz_eqn))
                                                .subs(e2d(self.sinbeta_pxpz_eqn))
                                                .subs({Abs(px):px}) ) )
        xiv_eqn = self.xiv_varphi_pxpz_eqn
        px_xiv_varphi_eqn = simplify(
            Eq( ((xiv_eqn.subs({Abs(px):px})).rhs)**eta_dbldenom - xiv_eqn.lhs**eta_dbldenom , 0)
                            .subs(e2d(self.pz_xiv_eqn))
                   )
        # HACK!!  Get rid of xiv**2 multiplier... should be a cleaner way of doing this
        self.px_xiv_varphi_eqn = factor(Eq(px_xiv_varphi_eqn.lhs/xiv**2,0))
        self.eta_dbldenom = eta_dbldenom


    def define_varphi_model_eqn(self):
        r"""
        Define flow component of erosion model function


        Attributes:
            varphi_model_ramp_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`\varphi{\left(\mathbf{r} \right)} = \varphi_0 \left(\varepsilon + \left(\dfrac{x_{1} - {r}^x}{x_{1}}\right)^{2 \mu}\right)`
            varphi_model_rampflat_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                    :math:`` TBD
            varphi_rx_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                specific choice of :math:`\varphi` model from the above

                - pure "channel" model `varphi_model_ramp_eqn` if `self.varphi_type=='ramp'`

                - "hillslope-channel" model `varphi_model_rampflat_eqn` if `self.varphi_type=='ramp-flat'`

        """
        # The implicit assumption here is that upstream area A ~ x^2, which will not be true
        #   for a "hillslope" component, and for which we should have a transition to A ~ x
        self.varphi_model_ramp_eqn = Eq(varphi_r, varphi_0*((x/x_1)**(mu*2) + varepsilon)).subs({x:x_1-rx})
        self.varphi_model_rampmu_chi0_eqn = Eq(varphi_r, varphi_0*((x/x_1)**(mu*2) + varepsilon)).subs({x:x_1-rx})
        self.varphi_model_rampflat_eqn = Eq(varphi_r, simplify(
            varphi_0*(  (chi/(x_1))*integrate(1/(1+sy.exp(-x/x_sigma)),x) + 1 )
                                .subs({x:-rx+x_1}) ))
        smooth_step_fn = 1/(1+exp(((x_1-x_h)-x)/x_sigma))
        # smooth_break_fn = (1+(chi/(x_1))**mu*integrate(smooth_step_fn,x))
        # TODO: fix deprecated chi usage
        smooth_break_fn = simplify( ((chi/(x_1))*(sy.integrate(smooth_step_fn,x))-chi*(1-x_h/x_1)+1)**(mu*2) )
        self.varphi_model_rampflatmu_eqn = Eq(varphi_r, simplify(
                    varphi_0*smooth_break_fn.subs({x:x_1-x})
                                .subs({x:rx}) ))
        if self.varphi_type=='ramp':
            varphi_model_eqn = self.varphi_model_ramp_eqn
        elif self.varphi_type=='ramp-flat':
            if self.mu==Rational(1,2):
                varphi_model_eqn = self.varphi_model_rampflat_eqn
            else:
                varphi_model_eqn = self.varphi_model_rampflatmu_eqn
        else:
            raise ValueError('Unknown flow model')
        self.varphi_rx_eqn = varphi_model_eqn


    def define_varphi_related_eqns(self):
        r"""
        Define further equations related to normal slowness :math:`p`


        Attributes:
            p_varphi_beta_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`p = \dfrac{1}{\varphi(\mathbf{r})|\sin\beta|^\eta}`
            p_varphi_pxpz_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`\sqrt{p_{x}^{2} + p_{z}^{2}} = \dfrac{\left(  {\sqrt{p_{x}^{2} + p_{z}^{2}}}  \right)^{\eta}}{\varphi{\left(\mathbf{r} \right)}{p_{x}}^\eta}`
            p_rx_pxpz_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`\sqrt{p_{x}^{2} + p_{z}^{2}}
                = \dfrac{p_{x}^{- \eta} x_{1}^{2 \mu} \left(p_{x}^{2} + p_{z}^{2}\right)^{\frac{\eta}{2}}}{\varphi_0 \left(\varepsilon x_{1}^{2 \mu} + \left(x_{1} - {r}^x\right)^{2 \mu}\right)}`
            p_rx_tanbeta_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`\sqrt{p_{x}^{2} + \dfrac{p_{x}^{2}}{\tan^{2}{\left(\beta \right)}}}
                = \dfrac{p_{x}^{- \eta} x_{1}^{2 \mu} \left(p_{x}^{2}
                + \dfrac{p_{x}^{2}}{\tan^{2}{\left(\beta \right)}}\right)^{\frac{\eta}{2}}}{\varphi_0 \left(\varepsilon x_{1}^{2 \mu} + \left(x_{1} - {r}^x\right)^{2 \mu}\right)}`
            px_beta_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`p_{x} = \dfrac{p_{x}^{- \eta} x_{1}^{2 \mu} \left(p_{x}^{2}
                + \dfrac{p_{x}^{2}}{\tan^{2}{\left(\beta \right)}}\right)^{\frac{\eta}{2}} \sin{\left(\beta \right)}}{\varphi_0 \left(\varepsilon x_{1}^{2 \mu} + \left(x_{1} - {r}^x\right)^{2 \mu}\right)}`
            pz_beta_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`p_{z} = - \dfrac{p_{x}^{- \eta} x_{1}^{2 \mu} \left(p_{x}^{2}
                + \dfrac{p_{x}^{2}}{\tan^{2}{\left(\beta \right)}}\right)^{\frac{\eta}{2}} \cos{\left(\beta \right)}}{\varphi_0 \left(\varepsilon x_{1}^{2 \mu} + \left(x_{1} - {r}^x\right)^{2 \mu}\right)}`
            xiv_pxpz_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`\xi^{\downarrow} = \dfrac{p_z}{p_x^{2} + p_z^{2}}`
            px_varphi_beta_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`p_{x} = \dfrac{\sin{\left(\beta \right)} \left|{\sin{\left(\beta \right)}}\right|^{- \eta}}{\varphi{\left(\mathbf{r} \right)}}`
            pz_varphi_beta_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`p_{z} = - \dfrac{\cos{\left(\beta \right)} \left|{\sin{\left(\beta \right)}}\right|^{- \eta}}{\varphi{\left(\mathbf{r} \right)}}`
            px_varphi_rx_beta_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`p_{x} = \dfrac{\sin{\left(\beta \right)} \left|{\sin{\left(\beta \right)}}\right|^{- \eta}}{\varphi_0 \left(\varepsilon + \left(\dfrac{x_{1} - {r}^x}{x_{1}}\right)^{2 \mu}\right)}`
            pz_varphi_rx_beta_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`p_{z} = - \dfrac{\cos{\left(\beta \right)} \left|{\sin{\left(\beta \right)}}\right|^{- \eta}}{\varphi_0 \left(\varepsilon + \left(\dfrac{x_{1} - {r}^x}{x_{1}}\right)^{2 \mu}\right)}`
        """
        self.p_varphi_beta_eqn  = self.p_xi_eqn.subs(e2d(self.xi_varphi_beta_eqn))
        # Note force px >= 0
        self.p_varphi_pxpz_eqn  = ( self.p_varphi_beta_eqn
                                          .subs(e2d(self.tanbeta_pxpz_eqn))
                                          .subs(e2d(self.sinbeta_pxpz_eqn))
                                          .subs(e2d(self.p_norm_pxpz_eqn))
                                          .subs({Abs(px):px})
                                        )
        # Don't do this simplification step because it messes up later calc of rdotz_on_rdotx_eqn etc
        # if self.eta==1 and self.beta_type=='sin':
        #     self.p_varphi_pxpz_eqn = simplify(Eq(self.p_varphi_pxpz_eqn.lhs/sqrt(px**2+pz**2),
        #                                     self.p_varphi_pxpz_eqn.rhs/sqrt(px**2+pz**2)))

        self.p_rx_pxpz_eqn = simplify( self.p_varphi_pxpz_eqn.subs({varphi_r:self.varphi_rx_eqn.rhs}) )
        self.p_rx_tanbeta_eqn = self.p_rx_pxpz_eqn.subs({pz:self.pz_px_tanbeta_eqn.rhs})
        self.px_beta_eqn = Eq(px, self.p_rx_tanbeta_eqn.rhs * sin(beta) )
        self.pz_beta_eqn = Eq(pz, -self.p_rx_tanbeta_eqn.rhs * cos(beta) )
        self.xiv_pxpz_eqn = simplify(Eq(xiv,-cos(beta)/p)
               .subs({cos(beta):1/sqrt(1+tan(beta)**2)})
               .subs({self.tanbeta_pxpz_eqn.lhs:self.tanbeta_pxpz_eqn.rhs})
               .subs({self.p_norm_pxpz_eqn.lhs:self.p_norm_pxpz_eqn.rhs}))

        tmp = self.xi_varphi_beta_eqn.subs(e2d(self.xi_p_eqn)).subs(e2d(self.p_pz_cosbeta_eqn))
        self.pz_varphi_beta_eqn = Eq(pz, solve(tmp,pz)[0])
        tmp = self.pz_varphi_beta_eqn.subs(e2d(self.pz_px_tanbeta_eqn))
        self.px_varphi_beta_eqn = Eq(px, solve(tmp,px)[0])
        self.pz_varphi_rx_beta_eqn = self.pz_varphi_beta_eqn.subs(e2d(self.varphi_rx_eqn))
        self.px_varphi_rx_beta_eqn = self.px_varphi_beta_eqn.subs(e2d(self.varphi_rx_eqn))


    def define_Fstar_eqns(self):
        r"""
        Define the fundamental function

        Attributes:
            Okubo_Fstar_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`\dfrac{\sqrt{p_{x}^{2} + p_{z}^{2}}}{F^{*}} = \dfrac{p_{x}^{- \eta} \left(p_{x}^{2} + p_{z}^{2}\right)^{\frac{\eta}{2}}}{\varphi{\left(\mathbf{r} \right)}}`
            Fstar_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`F^{*} = p_{x}^{\eta} \left(p_{x}^{2} + p_{z}^{2}\right)^{\frac{1}{2} - \frac{\eta}{2}} \varphi{\left(\mathbf{r} \right)}`
        """
        # Note force px >= 0
        self.Okubo_Fstar_eqn = simplify( Eq(self.p_norm_pxpz_eqn.rhs/Fstar, self.p_varphi_pxpz_eqn.rhs, ) \
                                            .subs({Abs(px):px,sy.sign(px):1}) )
        self.Fstar_eqn = Eq(Fstar, (solve(self.Okubo_Fstar_eqn,Fstar)[0]).subs({varphi_rx:varphi})) \
                                            .subs({Abs(px):px,sy.sign(px):1})


    def define_H_eqns(self):
        r"""
        Define the Hamiltonian


        Attributes:
            H_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`H = \dfrac{p_{x}^{2 \eta} \left(p_{x}^{2} + p_{z}^{2}\right)^{1 - \eta} \varphi^{2}{\left(\mathbf{r} \right)}}{2}`
            H_varphi_rx_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`H = \dfrac{\varphi_0^{2} p_{x}^{2 \eta} x_{1}^{- 4 \mu} \left(p_{x}^{2} + p_{z}^{2}\right)^{1 - \eta} \left(\varepsilon x_{1}^{2 \mu} + \left(x_{1} - {r}^x\right)^{2 \mu}\right)^{2}}{2}`
        """
        self.H_eqn =  ( Eq( H, simplify(self.Fstar_eqn.rhs**2/2) )
                                # .subs({Abs(px):px,sy.sign(px):1})
                            )
        self.H_varphi_rx_eqn = simplify(self.H_eqn.subs(varphi_r,self.varphi_rx_eqn.rhs))


    def define_rdot_eqns(self):
        r"""
        Define equations for :math:`\dot{r}`, the rate of change of position



        Attributes:
            rdotx_rdot_alpha_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`v^{x} = v \cos{\left(\alpha \right)}`
            rdotz_rdot_alpha_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`v^{z} = v \sin{\left(\alpha \right)}`
            rdotx_pxpz_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`v^{x} = p_{x}^{2 \eta - 1} \left(p_{x}^{2} + p_{z}^{2}\right)^{- \eta} \left(\eta p_{z}^{2} + p_{x}^{2}\right) \varphi^{2}{\left(\mathbf{r} \right)}`
            rdotz_pxpz_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`v^{z} = - p_{x}^{2 \eta} p_{z} \left(\eta - 1\right) \left(p_{x}^{2} + p_{z}^{2}\right)^{- \eta} \varphi^{2}{\left(\mathbf{r} \right)}`
            rdotz_on_rdotx_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`\dfrac{v^{z}}{v^{x}} = - \dfrac{p_{x} p_{z} \left(\eta - 1\right)}{\eta p_{z}^{2} + p_{x}^{2}}`
            rdotz_on_rdotx_tanbeta_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`\dfrac{v^{z}}{v^{x}} =   \dfrac{\left(\eta - 1\right) \tan{\left(\beta \right)}}{\eta + \tan^{2}{\left(\beta \right)}}`
            rdot_vec_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`\mathbf{v} = \left[\begin{matrix}p_{x}^{2 \eta - 1} \left(p_{x}^{2} + p_{z}^{2}\right)^{- \eta} \left(\eta p_{z}^{2} + p_{x}^{2}\right) \varphi^{2}{\left(\mathbf{r} \right)}\\- p_{x}^{2 \eta} p_{z} \left(\eta - 1\right) \left(p_{x}^{2} + p_{z}^{2}\right)^{- \eta} \varphi^{2}{\left(\mathbf{r} \right)}\end{matrix}\right]`
            rdot_p_unity_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`p_{x} v^{x} + p_{z} v^{z} = 1`
        """
        self.rdotx_rdot_alpha_eqn = Eq( rdotx, rdot*cos(alpha) )
        self.rdotz_rdot_alpha_eqn = Eq( rdotz, rdot*sin(alpha) )
        self.rdotx_pxpz_eqn = simplify( Eq(rdotx, sy.diff(self.H_eqn.rhs,px)) )
                                # simplify(sy.diff(self.H_eqn.rhs,px)).subs({Abs(px):px,sy.sign(px):1}) ) )
        self.rdotz_pxpz_eqn = simplify( Eq( rdotz, sy.diff(self.H_eqn.rhs,pz)) )
        # self.rdotz_pxpz_eqn = simplify( simplify( Eq( rdotz, simplify(sy.diff(self.H_eqn.rhs,pz))\
        #                                 .subs({Abs(px):px,sy.sign(px):1}) ) )
        #                                     .subs({px:pxp}) ) \
        #                                         .subs({pxp:px})
        self.rdotz_on_rdotx_eqn = factor( Eq( rdotz/rdotx,
                                        simplify( (self.rdotz_pxpz_eqn.rhs/self.rdotx_pxpz_eqn.rhs) ) ).subs({Abs(px):px}) )
        self.rdotz_on_rdotx_tanbeta_eqn = factor( self.rdotz_on_rdotx_eqn.subs({px:self.px_pz_tanbeta_eqn.rhs}) )
        self.rdot_vec_eqn = Eq(rdotvec,Matrix([self.rdotx_pxpz_eqn.rhs, self.rdotz_pxpz_eqn.rhs]))
        self.rdot_p_unity_eqn = Eq( rdotx*px+rdotz*pz, 1)


    def define_pdot_eqns(self):
        r"""
        Define equations for :math:`\dot{p}`, the rate of change of normal slowness


        Attributes:
            pdotx_pxpz_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`\dot{p}_x = 2 \mu \varphi_0^{2} p_{x}^{2 \eta} x_{1}^{- 4 \mu} \left(p_{x}^{2} + p_{z}^{2}\right)^{1 - \eta}
                \left(x_{1} - {r}^x\right)^{2 \mu - 1} \left(\varepsilon x_{1}^{2 \mu} + \left(x_{1} - {r}^x\right)^{2 \mu}\right)`
            pdotz_pxpz_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`\dot{p}_z = 0`
            pdot_covec_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`\mathbf{\dot{\widetilde{p}}} = \left[\begin{matrix}2 \mu \varphi_0^{2} p_{x}^{2 \eta} x_{1}^{- 4 \mu}
                \left(p_{x}^{2} + p_{z}^{2}\right)^{1 - \eta} \left(x_{1} - {r}^x\right)^{2 \mu - 1}
                \left(\varepsilon x_{1}^{2 \mu} + \left(x_{1} - {r}^x\right)^{2 \mu}\right) & 0\end{matrix}\right]`
        """
        self.pdotx_pxpz_eqn = simplify(Eq(pdotx, (-diff(self.H_varphi_rx_eqn.rhs,rx)) ))\
                                .subs({Abs(pz):-pz,Abs(px):px,Abs(px*pz):-px*pz,Abs(px/pz):-px/pz})
        self.pdotz_pxpz_eqn = simplify(Eq(pdotz,
                (0*diff(self.varphi_rx_eqn.rhs,rx)*(-self.tanbeta_pxpz_eqn.rhs)*self.H_eqn.rhs/varphi_r) ))
        self.pdot_covec_eqn = Eq(pdotcovec, Matrix([[self.pdotx_pxpz_eqn.rhs], [self.pdotz_pxpz_eqn.rhs]]).T)


    def define_Hamiltons_eqns(self):
        r"""
        Define Hamilton's equations


        Attributes:
            hamiltons_eqns (:class:`sympy.Matrix <sympy.matrices.immutable.ImmutableDenseMatrix>` of :class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`\left[\begin{matrix}\
                \dot{r}^x = \varphi_0^{2} p_{x}^{2 \eta - 1} x_{1}^{- 4 \mu} \left(p_{x}^{2} + p_{z}^{2}\right)^{- \eta} \left(\eta p_{z}^{2} + p_{x}^{2}\right)
                \left(\varepsilon x_{1}^{2 \mu} + \left(x_{1} - {r}^x\right)^{2 \mu}\right)^{2}\\
                \dot{r}^z = - \varphi_0^{2} p_{x}^{2 \eta} p_{z} x_{1}^{- 4 \mu} \left(\eta - 1\right) \left(p_{x}^{2} + p_{z}^{2}\right)^{- \eta}
                \left(\varepsilon x_{1}^{2 \mu} + \left(x_{1} - {r}^x\right)^{2 \mu}\right)^{2}\\
                \dot{p}_x = 2 \mu \varphi_0^{2} p_{x}^{2 \eta} x_{1}^{- 4 \mu} \left(p_{x}^{2} + p_{z}^{2}\right)^{1 - \eta} \left(x_{1} - {r}^x\right)^{2 \mu - 1}
                \left(\varepsilon x_{1}^{2 \mu} + \left(x_{1} - {r}^x\right)^{2 \mu}\right)\\
                \dot{p}_z = 0
                \end{matrix}\right]`
        """
        self.hamiltons_eqns = Matrix(
             (factor(simplify(self.rdotx_pxpz_eqn.subs(e2d(self.varphi_rx_eqn))).subs({rdotx:rdotx_true, rdotz:rdotz_true})).subs({Abs(px):px}),
              factor(simplify(self.rdotz_pxpz_eqn.subs(e2d(self.varphi_rx_eqn))).subs({rdotx:rdotx_true, rdotz:rdotz_true})).subs({Abs(px):px}),
              factor(simplify(self.pdotx_pxpz_eqn.subs(e2d(self.varphi_rx_eqn))).subs({rdotx:rdotx_true, rdotz:rdotz_true})).subs({Abs(px):px}),
              factor(simplify(self.pdotz_pxpz_eqn.subs(e2d(self.varphi_rx_eqn))).subs({rdotx:rdotx_true, rdotz:rdotz_true})).subs({Abs(px):px})
             ))


    def define_tanalpha_eqns(self):
        r"""
        Define equations for ray angle :math:`\tan(\alpha)`


        Attributes:
            tanalpha_pxpz_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`\tan{\left(\alpha \right)} = \dfrac{v^{z}}{v^{x}}`
            tanalpha_beta_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`\tan{\left(\alpha \right)} = - \dfrac{p_{x} p_{z} \left(\eta - 1\right)}{\eta p_{z}^{2} + p_{x}^{2}}`
            tanalpha_rdot_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`\tan{\left(\alpha \right)} = \dfrac{\left(\eta - 1\right) \tan{\left(\beta \right)}}{\eta + \tan^{2}{\left(\beta \right)}}`
        """
        self.tanalpha_rdot_eqn = Eq(simplify(self.rdotz_rdot_alpha_eqn.rhs/self.rdotx_rdot_alpha_eqn.rhs), rdotz/rdotx )
        self.tanalpha_pxpz_eqn = self.tanalpha_rdot_eqn \
                                    .subs({self.rdotz_on_rdotx_eqn.lhs:self.rdotz_on_rdotx_eqn.rhs})
        self.tanalpha_beta_eqn = self.tanalpha_rdot_eqn \
                                    .subs({self.rdotz_on_rdotx_eqn.lhs:self.rdotz_on_rdotx_tanbeta_eqn.rhs})


    def define_tanbeta_eqns(self, do_find_extrema=True):
        r"""
        Define equations for surface tilt angle :math:`\beta)`

        Args:
            do_find_extrema (bool) :
                find extremal values for :math:`\alpha`, and then find the corresponding value of :math:`\beta` at each extremum


        Attributes:
            beta_at_alpha_extremum_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`\beta_{\text{extremum}\{\alpha\}} = \operatorname{atan}{\left(\sqrt{\eta} \right)}`
            beta_at_alpha_extremum_numerical_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`\beta_{\text{extremum}\{\alpha\}} = 0.886077123792614`
            tanbeta_alpha_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`\tan{\left(\beta \right)} \
                = \dfrac{\eta - \sqrt{\eta^{2} - 4 \eta \tan^{2}{\left(\alpha \right)} - 2 \eta + 1} - 1}{2 \tan{\left(\alpha \right)}}`
        """
        eta_sub = {eta: self.eta}
        #TODO: this is a stationary point, not a min, so change name to minmax
        self.beta_at_alpha_extremum_eqn = None
        self.beta_at_alpha_extremum_numerical_eqn = None
        self.tanbeta_alpha_eqn = None

        if do_find_extrema:
            alpha_extrema = [simplify(soln) for soln in solve( Eq(diff(self.tanalpha_beta_eqn.rhs, beta),0), beta )]
            alpha_extrema_real_positive = [extremum for extremum in alpha_extrema
                                                if sy.im(extremum.subs(eta_sub))==0 and extremum.subs(eta_sub)>0]
            if alpha_extrema_real_positive != []:
                self.beta_at_alpha_extremum_eqn = Eq(beta_at_alpha_extremum, alpha_extrema_real_positive[0])
                self.beta_at_alpha_extremum_numerical_eqn = Eq(beta_at_alpha_extremum, (float(sy.N(self.beta_at_alpha_extremum_eqn.rhs.subs(eta_sub)))))
            elif alpha_extrema != []:
                self.beta_at_alpha_extremum_eqn = Eq(beta_at_alpha_extremum,alpha_extrema[0])
                self.beta_at_alpha_extremum_numerical_eqn = Eq(beta_at_alpha_extremum, sy.N(alpha_extrema[0].subs(eta_sub)))
                print('Warning: real positive root for beta not found')
            else:
                self.beta_at_alpha_extremum_eqn = Eq(beta_at_alpha_extremum,0)
                self.beta_at_alpha_extremum_numerical_eqn = Eq(beta_at_alpha_extremum.subs(eta_sub), 0)

        if self.eta==1 and self.beta_type=='sin':
            print(r'Cannot compute all $\beta$ equations for $\sin\beta$ model and $\eta=1$')
            return
        solns = sy.solve(self.tanalpha_beta_eqn.subs({tan(alpha):ta}),tan(beta))
        # # We get multiple roots for tan(beta), so guess which is real by evaluating it at an fairly arbitrary tan(alpha)
        self.tanbeta_alpha_eqn = Eq(tan(beta), simplify([soln for soln in solns
            if sy.im(soln.subs(ta,0).subs(eta_sub))==0 or sy.im(soln.subs(ta,0.01).subs(eta_sub))==0 or sy.im(soln.subs(ta,1).subs(eta_sub))==0
                                    ][0])).subs({ta:tan(alpha)})


    def define_g_eqns(self):
        r"""
        Define equations for the metric tensor :math:`g` and its dual  :math:`g^*`

        Attributes:
            gstar_varphi_pxpz_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`g^{*} = \left[\begin{matrix}\
                \dfrac{2 p_{x}^{3} \varphi^{2}{\left(\mathbf{r} \right)}}{\left(p_{x}^{2} + p_{z}^{2}\right)^{\frac{3}{2}}} \
                - \dfrac{3 p_{x}^{3} \left(p_{x}^{2} + \dfrac{3 p_{z}^{2}}{2}\right) \varphi^{2}{\left(\mathbf{r} \right)}}{\left(p_{x}^{2} + p_{z}^{2}\right)^{\frac{5}{2}}} \
                + \dfrac{2 p_{x} \left(p_{x}^{2} + \dfrac{3 p_{z}^{2}}{2}\right) \varphi^{2}{\left(\mathbf{r} \right)}}{\left(p_{x}^{2} + p_{z}^{2}\right)^{\frac{3}{2}}} \
                & \dfrac{3 p_{x}^{4} p_{z} \varphi^{2}{\left(\mathbf{r} \right)}}{2 \left(p_{x}^{2} + p_{z}^{2}\right)^{\frac{5}{2}}} \
                - \dfrac{3 p_{x}^{2} p_{z} \varphi^{2}{\left(\mathbf{r} \right)}}{2 \left(p_{x}^{2} + p_{z}^{2}\right)^{\frac{3}{2}}}\\ \
                \dfrac{3 p_{x}^{2} p_{z} \varphi^{2}{\left(\mathbf{r} \right)}}{\left(p_{x}^{2} + p_{z}^{2}\right)^{\frac{3}{2}}} \
                - \dfrac{3 p_{x}^{2} p_{z} \left(p_{x}^{2} + \dfrac{3 p_{z}^{2}}{2}\right) \varphi^{2}{\left(\mathbf{r} \right)}}{\left(p_{x}^{2} + p_{z}^{2}\right)^{\frac{5}{2}}} \
                & \dfrac{3 p_{x}^{3} p_{z}^{2} \varphi^{2}{\left(\mathbf{r} \right)}}{2 \left(p_{x}^{2} + p_{z}^{2}\right)^{\frac{5}{2}}} \
                - \dfrac{p_{x}^{3} \varphi^{2}{\left(\mathbf{r} \right)}}{2 \left(p_{x}^{2} + p_{z}^{2}\right)^{\frac{3}{2}}}\
                \end{matrix}\right]`
            det_gstar_varphi_pxpz_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`\det\left(g^*\right) \
                = \dfrac{p_{x}^{4} \left(- \dfrac{p_{x}^{2}}{2} \
                + \dfrac{3 p_{z}^{2}}{4}\right) \varphi^{4}{\left(\mathbf{r} \right)}}{p_{x}^{6} + 3 p_{x}^{4} p_{z}^{2} + 3 p_{x}^{2} p_{z}^{4} + p_{z}^{6}}`
            g_varphi_pxpz_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`g = \left[\begin{matrix}\
                \dfrac{2 \left(p_{x}^{2} - 2 p_{z}^{2}\right) \sqrt{p_{x}^{2} + p_{z}^{2}}}{p_{x} \left(2 p_{x}^{2} - 3 p_{z}^{2}\right) \varphi^{2}{\left(\mathbf{r} \right)}} \
                & - \dfrac{6 p_{z}^{3} \sqrt{p_{x}^{2} + p_{z}^{2}}}{p_{x}^{2} \left(2 p_{x}^{2} - 3 p_{z}^{2}\right) \varphi^{2}{\left(\mathbf{r} \right)}}\\ \
                - \dfrac{6 p_{z}^{3} \sqrt{p_{x}^{2} + p_{z}^{2}}}{p_{x}^{2} \left(2 p_{x}^{2} - 3 p_{z}^{2}\right) \varphi^{2}{\left(\mathbf{r} \right)}} \
                & - \dfrac{4 p_{x}^{6} + 14 p_{x}^{4} p_{z}^{2} + 22 p_{x}^{2} p_{z}^{4} + 12 p_{z}^{6}}{p_{x}^{3} \sqrt{p_{x}^{2} + p_{z}^{2}} \left(2 p_{x}^{2} - 3 p_{z}^{2}\right) \varphi^{2}{\left(\mathbf{r} \right)}}\
                \end{matrix}\right]`
            gstar_eigen_varphi_pxpz   (list of :class:`sympy.Expr <sympy.core.expr.Expr>`) :
                eigenvalues and eigenvectors of :math:`g^{*}` in one object
            gstar_eigenvalues   (:class:`sympy.Matrix <sympy.matrices.immutable.ImmutableDenseMatrix>`) :
                :math:`\left[\begin{matrix}\
                \dfrac{\varphi_0^{2} p_{x} x_{1}^{- 4 \mu} \left(\varepsilon x_{1}^{2 \mu} + \left(x_{1} - {r}^x\right)^{2 \mu}\right)^{2} \left(- 3 \left(p_{x}^{2} + p_{z}^{2}\right) \sqrt{p_{x}^{12} + 4 p_{x}^{10} p_{z}^{2} + 10 p_{x}^{8} p_{z}^{4} + 20 p_{x}^{6} p_{z}^{6} + 25 p_{x}^{4} p_{z}^{8} + 16 p_{x}^{2} p_{z}^{10} + 4 p_{z}^{12}} + \left(p_{x}^{2} + 6 p_{z}^{2}\right) \left(p_{x}^{6} + 3 p_{x}^{4} p_{z}^{2} + 3 p_{x}^{2} p_{z}^{4} + p_{z}^{6}\right)\right)}{4 \left(p_{x}^{2} + p_{z}^{2}\right)^{\frac{3}{2}} \left(p_{x}^{6} + 3 p_{x}^{4} p_{z}^{2} + 3 p_{x}^{2} p_{z}^{4} + p_{z}^{6}\right)}\\\
                \dfrac{\varphi_0^{2} p_{x} x_{1}^{- 4 \mu} \left(\varepsilon x_{1}^{2 \mu} + \left(x_{1} - {r}^x\right)^{2 \mu}\right)^{2} \left(3 \left(p_{x}^{2} + p_{z}^{2}\right) \sqrt{p_{x}^{12} + 4 p_{x}^{10} p_{z}^{2} + 10 p_{x}^{8} p_{z}^{4} + 20 p_{x}^{6} p_{z}^{6} + 25 p_{x}^{4} p_{z}^{8} + 16 p_{x}^{2} p_{z}^{10} + 4 p_{z}^{12}} + \left(p_{x}^{2} + 6 p_{z}^{2}\right) \left(p_{x}^{6} + 3 p_{x}^{4} p_{z}^{2} + 3 p_{x}^{2} p_{z}^{4} + p_{z}^{6}\right)\right)}{4 \left(p_{x}^{2} + p_{z}^{2}\right)^{\frac{3}{2}} \left(p_{x}^{6} + 3 p_{x}^{4} p_{z}^{2} + 3 p_{x}^{2} p_{z}^{4} + p_{z}^{6}\right)}\
                \end{matrix}\right]`
            gstar_eigenvectors   (list containing pair of :class:`sympy.Matrix <sympy.matrices.immutable.ImmutableDenseMatrix>`) :
                :math:`\left[\
                \begin{matrix}\dfrac{p_{x} p_{z}^{3} \left(p_{x}^{6} + 2 p_{x}^{4} p_{z}^{2} + 3 p_{x}^{2} p_{z}^{4} + 2 p_{z}^{6} + \sqrt{p_{x}^{12} + 4 p_{x}^{10} p_{z}^{2} + 10 p_{x}^{8} p_{z}^{4} + 20 p_{x}^{6} p_{z}^{6} + 25 p_{x}^{4} p_{z}^{8} + 16 p_{x}^{2} p_{z}^{10} + 4 p_{z}^{12}}\right)}{p_{x}^{10} + 3 p_{x}^{8} p_{z}^{2} + 7 p_{x}^{6} p_{z}^{4} + 11 p_{x}^{4} p_{z}^{6} + p_{x}^{4} \sqrt{p_{x}^{12} + 4 p_{x}^{10} p_{z}^{2} + 10 p_{x}^{8} p_{z}^{4} + 20 p_{x}^{6} p_{z}^{6} + 25 p_{x}^{4} p_{z}^{8} + 16 p_{x}^{2} p_{z}^{10} + 4 p_{z}^{12}} + 10 p_{x}^{2} p_{z}^{8} + p_{x}^{2} p_{z}^{2} \sqrt{p_{x}^{12} + 4 p_{x}^{10} p_{z}^{2} + 10 p_{x}^{8} p_{z}^{4} + 20 p_{x}^{6} p_{z}^{6} + 25 p_{x}^{4} p_{z}^{8} + 16 p_{x}^{2} p_{z}^{10} + 4 p_{z}^{12}} + 4 p_{z}^{10} + 2 p_{z}^{4} \sqrt{p_{x}^{12} + 4 p_{x}^{10} p_{z}^{2} + 10 p_{x}^{8} p_{z}^{4} + 20 p_{x}^{6} p_{z}^{6} + 25 p_{x}^{4} p_{z}^{8} + 16 p_{x}^{2} p_{z}^{10} + 4 p_{z}^{12}}}\\ \
                1 \
                \end{matrix}\
                \right] \\ \
                \left[\
                \begin{matrix}\dfrac{p_{x} p_{z}^{3} \left(p_{x}^{6} + 2 p_{x}^{4} p_{z}^{2} + 3 p_{x}^{2} p_{z}^{4} + 2 p_{z}^{6} - \sqrt{p_{x}^{12} + 4 p_{x}^{10} p_{z}^{2} + 10 p_{x}^{8} p_{z}^{4} + 20 p_{x}^{6} p_{z}^{6} + 25 p_{x}^{4} p_{z}^{8} + 16 p_{x}^{2} p_{z}^{10} + 4 p_{z}^{12}}\right)}{p_{x}^{10} + 3 p_{x}^{8} p_{z}^{2} + 7 p_{x}^{6} p_{z}^{4} + 11 p_{x}^{4} p_{z}^{6} - p_{x}^{4} \sqrt{p_{x}^{12} + 4 p_{x}^{10} p_{z}^{2} + 10 p_{x}^{8} p_{z}^{4} + 20 p_{x}^{6} p_{z}^{6} + 25 p_{x}^{4} p_{z}^{8} + 16 p_{x}^{2} p_{z}^{10} + 4 p_{z}^{12}} + 10 p_{x}^{2} p_{z}^{8} - p_{x}^{2} p_{z}^{2} \sqrt{p_{x}^{12} + 4 p_{x}^{10} p_{z}^{2} + 10 p_{x}^{8} p_{z}^{4} + 20 p_{x}^{6} p_{z}^{6} + 25 p_{x}^{4} p_{z}^{8} + 16 p_{x}^{2} p_{z}^{10} + 4 p_{z}^{12}} + 4 p_{z}^{10} - 2 p_{z}^{4} \sqrt{p_{x}^{12} + 4 p_{x}^{10} p_{z}^{2} + 10 p_{x}^{8} p_{z}^{4} + 20 p_{x}^{6} p_{z}^{6} + 25 p_{x}^{4} p_{z}^{8} + 16 p_{x}^{2} p_{z}^{10} + 4 p_{z}^{12}}}\\ \
                1 \
                \end{matrix}\right]`
        """
        self.gstar_varphi_pxpz_eqn = None
        self.det_gstar_varphi_pxpz_eqn = None
        self.g_varphi_pxpz_eqn = None
        self.gstar_eigen_varphi_pxpz = None
        self.gstar_eigenvalues = None
        self.gstar_eigenvectors = None

        eta_sub = {eta: self.eta}
        self.gstar_varphi_pxpz_eqn = Eq(gstar,
            factor( Matrix([diff(self.rdot_vec_eqn.rhs, self.p_covec_eqn.rhs[0]).T,
                              diff(self.rdot_vec_eqn.rhs, self.p_covec_eqn.rhs[1]).T]) )).subs(eta_sub)
        self.det_gstar_varphi_pxpz_eqn = Eq(det_gstar,(simplify(self.gstar_varphi_pxpz_eqn.rhs.subs(eta_sub).det())))
        if self.eta==1 and self.beta_type=='sin':
            print(r'Cannot compute all metric tensor $g^{ij}$ equations for $\sin\beta$ model and $\eta=1$')
            return
        self.g_varphi_pxpz_eqn = Eq(g, simplify( self.gstar_varphi_pxpz_eqn.rhs.subs(eta_sub).inverse() ))
        self.gstar_eigen_varphi_pxpz = self.gstar_varphi_pxpz_eqn.rhs.eigenvects()
        self.gstar_eigenvalues = simplify(
            Matrix([self.gstar_eigen_varphi_pxpz[0][0],
                    self.gstar_eigen_varphi_pxpz[1][0]])
                    .subs({varphi_r:self.varphi_rx_eqn.rhs}) )
        self.gstar_eigenvectors = (
            [simplify(Matrix(self.gstar_eigen_varphi_pxpz[0][2][0])
                            .subs({varphi_r:self.varphi_rx_eqn.rhs})),
             simplify(Matrix(self.gstar_eigen_varphi_pxpz[1][2][0])
                            .subs({varphi_r:self.varphi_rx_eqn.rhs}))] )


    def define_idtx_fgtx_eqns(self):
        r"""
        Define indicatrix and figuratrix equations



        Attributes:
            pz_cosbeta_varphi_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`p_{z}^{4} = \dfrac{\cos^{4}{\left(\beta \right)}}{\varphi^{4} \left(1 - \cos^{2}{\left(\beta \right)}\right)^{3}}`
            cosbetasqrd_pz_varphi_solns  (list of :class:`sympy.Expr <sympy.core.expr.Expr>`) :
                :math:`\left[
                -\frac{ \left(  -6 \varphi^{4} p_{z}^{4} \sqrt[3]{27 \varphi^{8} p_{z}^{8} - 18 \varphi^{4} p_{z}^{4}
                + \sqrt{729 \varphi^{16} p_{z}^{16} - 108 \varphi^{12} p_{z}^{12}} + 2} - 12 \sqrt[3]{2} \varphi^{4} p_{z}^{4}
                + 2^{\frac{2}{3}} \left(27 \varphi^{8} p_{z}^{8} - 18 \varphi^{4} p_{z}^{4}
                + \sqrt{729 \varphi^{16} p_{z}^{16} - 108 \varphi^{12} p_{z}^{12}} + 2\right)^{\frac{2}{3}}
                + 2 \sqrt[3]{27 \varphi^{8} p_{z}^{8} - 18 \varphi^{4} p_{z}^{4} + \sqrt{729 \varphi^{16} p_{z}^{16}
                - 108 \varphi^{12} p_{z}^{12}} + 2} + 2 \sqrt[3]{2} \right)
                }{6 \varphi^{4} p_{z}^{4} \sqrt[3]{27 \varphi^{8} p_{z}^{8}
                - 18 \varphi^{4} p_{z}^{4} + \sqrt{729 \varphi^{16} p_{z}^{16} - 108 \varphi^{12} p_{z}^{12}} + 2}}
                ,\dots \right]`
            fgtx_cossqrdbeta_pz_varphi_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`\cos^{2}{\left(\beta \right)}
                = - \frac{- 6 \varphi^{4} p_{z}^{4} \sqrt[3]{27 \varphi^{8} p_{z}^{8} - 18 \varphi^{4} p_{z}^{4}
                + \sqrt{729 \varphi^{16} p_{z}^{16} - 108 \varphi^{12} p_{z}^{12}} + 2} - 12 \sqrt[3]{2} \varphi^{4} p_{z}^{4}
                + 2^{\frac{2}{3}} \left(27 \varphi^{8} p_{z}^{8} - 18 \varphi^{4} p_{z}^{4} + \sqrt{729 \varphi^{16} p_{z}^{16}
                - 108 \varphi^{12} p_{z}^{12}} + 2\right)^{\frac{2}{3}} + 2 \sqrt[3]{27 \varphi^{8} p_{z}^{8}
                - 18 \varphi^{4} p_{z}^{4} + \sqrt{729 \varphi^{16} p_{z}^{16} - 108 \varphi^{12} p_{z}^{12}} + 2}
                + 2 \sqrt[3]{2}}{6 \varphi^{4} p_{z}^{4} \sqrt[3]{27 \varphi^{8} p_{z}^{8} - 18 \varphi^{4} p_{z}^{4}
                + \sqrt{729 \varphi^{16} p_{z}^{16} - 108 \varphi^{12} p_{z}^{12}} + 2}}`
            fgtx_tanbeta_pz_varphi_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`\tan{\left(\beta \right)}
                = \sqrt{\frac{- 12 \sqrt[3]{2} \varphi^{4} p_{z}^{4} + 2^{\frac{2}{3}} \left(27 \varphi^{8} p_{z}^{8}
                - 18 \varphi^{4} p_{z}^{4} + \sqrt{729 \varphi^{16} p_{z}^{16} - 108 \varphi^{12} p_{z}^{12}} + 2\right)^{\frac{2}{3}}
                + 2 \sqrt[3]{27 \varphi^{8} p_{z}^{8} - 18 \varphi^{4} p_{z}^{4} + \sqrt{729 \varphi^{16} p_{z}^{16}
                - 108 \varphi^{12} p_{z}^{12}} + 2} + 2 \sqrt[3]{2}}{6 \varphi^{4} p_{z}^{4} \sqrt[3]{27 \varphi^{8} p_{z}^{8}
                - 18 \varphi^{4} p_{z}^{4} + \sqrt{729 \varphi^{16} p_{z}^{16} - 108 \varphi^{12} p_{z}^{12}} + 2}
                + 12 \sqrt[3]{2} \varphi^{4} p_{z}^{4} - 2^{\frac{2}{3}} \left(27 \varphi^{8} p_{z}^{8}
                - 18 \varphi^{4} p_{z}^{4} + \sqrt{729 \varphi^{16} p_{z}^{16} - 108 \varphi^{12} p_{z}^{12}} + 2\right)^{\frac{2}{3}}
                - 2 \sqrt[3]{27 \varphi^{8} p_{z}^{8} - 18 \varphi^{4} p_{z}^{4} + \sqrt{729 \varphi^{16} p_{z}^{16}
                - 108 \varphi^{12} p_{z}^{12}} + 2} - 2 \sqrt[3]{2}}}`
            fgtx_px_pz_varphi_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`p_{x}
                = - p_{z} \sqrt{\frac{- 12 \sqrt[3]{2} \varphi^{4} p_{z}^{4} + 2^{\frac{2}{3}} \left(27 \varphi^{8} p_{z}^{8}
                - 18 \varphi^{4} p_{z}^{4} + \sqrt{729 \varphi^{16} p_{z}^{16} - 108 \varphi^{12} p_{z}^{12}} + 2\right)^{\frac{2}{3}}
                + 2 \sqrt[3]{27 \varphi^{8} p_{z}^{8} - 18 \varphi^{4} p_{z}^{4} + \sqrt{729 \varphi^{16} p_{z}^{16}
                - 108 \varphi^{12} p_{z}^{12}} + 2} + 2 \sqrt[3]{2}}{6 \varphi^{4} p_{z}^{4} \sqrt[3]{27 \varphi^{8} p_{z}^{8}
                - 18 \varphi^{4} p_{z}^{4} + \sqrt{729 \varphi^{16} p_{z}^{16} - 108 \varphi^{12} p_{z}^{12}} + 2}
                + 12 \sqrt[3]{2} \varphi^{4} p_{z}^{4} - 2^{\frac{2}{3}} \left(27 \varphi^{8} p_{z}^{8}
                - 18 \varphi^{4} p_{z}^{4} + \sqrt{729 \varphi^{16} p_{z}^{16} - 108 \varphi^{12} p_{z}^{12}} + 2\right)^{\frac{2}{3}}
                - 2 \sqrt[3]{27 \varphi^{8} p_{z}^{8} - 18 \varphi^{4} p_{z}^{4} + \sqrt{729 \varphi^{16} p_{z}^{16}
                - 108 \varphi^{12} p_{z}^{12}} + 2} - 2 \sqrt[3]{2}}}`
            idtx_rdotx_pz_varphi_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`{r}^x = \dfrac{\sqrt{6} \left(- 81 \cdot 2^{\frac{2}{3}} \varphi^{12} p_{z}^{12} \sqrt[3]{27 \varphi^{8} p_{z}^{8} + 3 \sqrt{3} \varphi^{6} p_{z}^{6} \sqrt{27 \varphi^{4} p_{z}^{4} - 4} - 18 \varphi^{4} p_{z}^{4} + 2} - 378 \varphi^{12} p_{z}^{12} - 9 \cdot 2^{\frac{2}{3}} \sqrt{3} \varphi^{10} p_{z}^{10} \sqrt{27 \varphi^{4} p_{z}^{4} - 4} \sqrt[3]{27 \varphi^{8} p_{z}^{8} + 3 \sqrt{3} \varphi^{6} p_{z}^{6} \sqrt{27 \varphi^{4} p_{z}^{4} - 4} - 18 \varphi^{4} p_{z}^{4} + 2} - 42 \sqrt{3} \varphi^{10} p_{z}^{10} \sqrt{27 \varphi^{4} p_{z}^{4} - 4} + 45 \sqrt[3]{2} \varphi^{8} p_{z}^{8} \left(27 \varphi^{8} p_{z}^{8} + 3 \sqrt{3} \varphi^{6} p_{z}^{6} \sqrt{27 \varphi^{4} p_{z}^{4} - 4} - 18 \varphi^{4} p_{z}^{4} + 2\right)^{\frac{2}{3}} + 96 \cdot 2^{\frac{2}{3}} \varphi^{8} p_{z}^{8} \sqrt[3]{27 \varphi^{8} p_{z}^{8} + 3 \sqrt{3} \varphi^{6} p_{z}^{6} \sqrt{27 \varphi^{4} p_{z}^{4} - 4} - 18 \varphi^{4} p_{z}^{4} + 2} + 306 \varphi^{8} p_{z}^{8} + \sqrt[3]{2} \sqrt{3} \varphi^{6} p_{z}^{6} \sqrt{27 \varphi^{4} p_{z}^{4} - 4} \left(27 \varphi^{8} p_{z}^{8} + 3 \sqrt{3} \varphi^{6} p_{z}^{6} \sqrt{27 \varphi^{4} p_{z}^{4} - 4} - 18 \varphi^{4} p_{z}^{4} + 2\right)^{\frac{2}{3}} + 2 \cdot 2^{\frac{2}{3}} \sqrt{3} \varphi^{6} p_{z}^{6} \sqrt{27 \varphi^{4} p_{z}^{4} - 4} \sqrt[3]{27 \varphi^{8} p_{z}^{8} + 3 \sqrt{3} \varphi^{6} p_{z}^{6} \sqrt{27 \varphi^{4} p_{z}^{4} - 4} - 18 \varphi^{4} p_{z}^{4} + 2} + 6 \sqrt{3} \varphi^{6} p_{z}^{6} \sqrt{27 \varphi^{4} p_{z}^{4} - 4} - 20 \sqrt[3]{2} \varphi^{4} p_{z}^{4} \left(27 \varphi^{8} p_{z}^{8} + 3 \sqrt{3} \varphi^{6} p_{z}^{6} \sqrt{27 \varphi^{4} p_{z}^{4} - 4} - 18 \varphi^{4} p_{z}^{4} + 2\right)^{\frac{2}{3}} - 26 \cdot 2^{\frac{2}{3}} \varphi^{4} p_{z}^{4} \sqrt[3]{27 \varphi^{8} p_{z}^{8} + 3 \sqrt{3} \varphi^{6} p_{z}^{6} \sqrt{27 \varphi^{4} p_{z}^{4} - 4} - 18 \varphi^{4} p_{z}^{4} + 2} - 64 \varphi^{4} p_{z}^{4} + 2 \sqrt[3]{2} \left(27 \varphi^{8} p_{z}^{8} + 3 \sqrt{3} \varphi^{6} p_{z}^{6} \sqrt{27 \varphi^{4} p_{z}^{4} - 4} - 18 \varphi^{4} p_{z}^{4} + 2\right)^{\frac{2}{3}} + 2 \cdot 2^{\frac{2}{3}} \sqrt[3]{27 \varphi^{8} p_{z}^{8} + 3 \sqrt{3} \varphi^{6} p_{z}^{6} \sqrt{27 \varphi^{4} p_{z}^{4} - 4} - 18 \varphi^{4} p_{z}^{4} + 2} + 4\right)}{72 \varphi^{4} p_{z}^{5} \left(\frac{\sqrt[3]{27 \varphi^{8} p_{z}^{8} + 3 \sqrt{3} \varphi^{6} p_{z}^{6} \sqrt{27 \varphi^{4} p_{z}^{4} - 4} - 18 \varphi^{4} p_{z}^{4} + 2}}{6 \varphi^{4} p_{z}^{4} \sqrt[3]{27 \varphi^{8} p_{z}^{8} + 3 \sqrt{3} \varphi^{6} p_{z}^{6} \sqrt{27 \varphi^{4} p_{z}^{4} - 4} - 18 \varphi^{4} p_{z}^{4} + 2} + 12 \sqrt[3]{2} \varphi^{4} p_{z}^{4} - 2^{\frac{2}{3}} \left(27 \varphi^{8} p_{z}^{8} + 3 \sqrt{3} \varphi^{6} p_{z}^{6} \sqrt{27 \varphi^{4} p_{z}^{4} - 4} - 18 \varphi^{4} p_{z}^{4} + 2\right)^{\frac{2}{3}} - 2 \sqrt[3]{27 \varphi^{8} p_{z}^{8} + 3 \sqrt{3} \varphi^{6} p_{z}^{6} \sqrt{27 \varphi^{4} p_{z}^{4} - 4} - 18 \varphi^{4} p_{z}^{4} + 2} - 2 \sqrt[3]{2}}\right)^{\frac{3}{2}} \sqrt[3]{27 \varphi^{8} p_{z}^{8} + 3 \sqrt{3} \varphi^{6} p_{z}^{6} \sqrt{27 \varphi^{4} p_{z}^{4} - 4} - 18 \varphi^{4} p_{z}^{4} + 2} \left(- 54 \cdot 2^{\frac{2}{3}} \varphi^{12} p_{z}^{12} - 6 \cdot 2^{\frac{2}{3}} \sqrt{3} \varphi^{10} p_{z}^{10} \sqrt{27 \varphi^{4} p_{z}^{4} - 4} + 6 \varphi^{8} p_{z}^{8} \left(27 \varphi^{8} p_{z}^{8} + 3 \sqrt{3} \varphi^{6} p_{z}^{6} \sqrt{27 \varphi^{4} p_{z}^{4} - 4} - 18 \varphi^{4} p_{z}^{4} + 2\right)^{\frac{2}{3}} + 33 \sqrt[3]{2} \varphi^{8} p_{z}^{8} \sqrt[3]{27 \varphi^{8} p_{z}^{8} + 3 \sqrt{3} \varphi^{6} p_{z}^{6} \sqrt{27 \varphi^{4} p_{z}^{4} - 4} - 18 \varphi^{4} p_{z}^{4} + 2} + 78 \cdot 2^{\frac{2}{3}} \varphi^{8} p_{z}^{8} + \sqrt[3]{2} \sqrt{3} \varphi^{6} p_{z}^{6} \sqrt{27 \varphi^{4} p_{z}^{4} - 4} \sqrt[3]{27 \varphi^{8} p_{z}^{8} + 3 \sqrt{3} \varphi^{6} p_{z}^{6} \sqrt{27 \varphi^{4} p_{z}^{4} - 4} - 18 \varphi^{4} p_{z}^{4} + 2} + 2 \cdot 2^{\frac{2}{3}} \sqrt{3} \varphi^{6} p_{z}^{6} \sqrt{27 \varphi^{4} p_{z}^{4} - 4} - 12 \varphi^{4} p_{z}^{4} \left(27 \varphi^{8} p_{z}^{8} + 3 \sqrt{3} \varphi^{6} p_{z}^{6} \sqrt{27 \varphi^{4} p_{z}^{4} - 4} - 18 \varphi^{4} p_{z}^{4} + 2\right)^{\frac{2}{3}} - 18 \sqrt[3]{2} \varphi^{4} p_{z}^{4} \sqrt[3]{27 \varphi^{8} p_{z}^{8} + 3 \sqrt{3} \varphi^{6} p_{z}^{6} \sqrt{27 \varphi^{4} p_{z}^{4} - 4} - 18 \varphi^{4} p_{z}^{4} + 2} - 24 \cdot 2^{\frac{2}{3}} \varphi^{4} p_{z}^{4} + 2 \left(27 \varphi^{8} p_{z}^{8} + 3 \sqrt{3} \varphi^{6} p_{z}^{6} \sqrt{27 \varphi^{4} p_{z}^{4} - 4} - 18 \varphi^{4} p_{z}^{4} + 2\right)^{\frac{2}{3}} + 2 \sqrt[3]{2} \sqrt[3]{27 \varphi^{8} p_{z}^{8} + 3 \sqrt{3} \varphi^{6} p_{z}^{6} \sqrt{27 \varphi^{4} p_{z}^{4} - 4} - 18 \varphi^{4} p_{z}^{4} + 2} + 2 \cdot 2^{\frac{2}{3}}\right)}`
            idtx_rdotz_pz_varphi_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`{r}^z = \dfrac{\sqrt{6} \sqrt{\frac{- 12 \sqrt[3]{2} \varphi^{4} p_{z}^{4} + 2^{\frac{2}{3}} \left(27 \varphi^{8} p_{z}^{8} + 3 \sqrt{3} \varphi^{6} p_{z}^{6} \sqrt{27 \varphi^{4} p_{z}^{4} - 4} - 18 \varphi^{4} p_{z}^{4} + 2\right)^{\frac{2}{3}} + 2 \sqrt[3]{27 \varphi^{8} p_{z}^{8} + 3 \sqrt{3} \varphi^{6} p_{z}^{6} \sqrt{27 \varphi^{4} p_{z}^{4} - 4} - 18 \varphi^{4} p_{z}^{4} + 2} + 2 \sqrt[3]{2}}{6 \varphi^{4} p_{z}^{4} \sqrt[3]{27 \varphi^{8} p_{z}^{8} + 3 \sqrt{3} \varphi^{6} p_{z}^{6} \sqrt{27 \varphi^{4} p_{z}^{4} - 4} - 18 \varphi^{4} p_{z}^{4} + 2} + 12 \sqrt[3]{2} \varphi^{4} p_{z}^{4} - 2^{\frac{2}{3}} \left(27 \varphi^{8} p_{z}^{8} + 3 \sqrt{3} \varphi^{6} p_{z}^{6} \sqrt{27 \varphi^{4} p_{z}^{4} - 4} - 18 \varphi^{4} p_{z}^{4} + 2\right)^{\frac{2}{3}} - 2 \sqrt[3]{27 \varphi^{8} p_{z}^{8} + 3 \sqrt{3} \varphi^{6} p_{z}^{6} \sqrt{27 \varphi^{4} p_{z}^{4} - 4} - 18 \varphi^{4} p_{z}^{4} + 2} - 2 \sqrt[3]{2}}} \left(27 \cdot 2^{\frac{2}{3}} \varphi^{8} p_{z}^{8} + 3 \cdot 2^{\frac{2}{3}} \sqrt{3} \varphi^{6} p_{z}^{6} \sqrt{27 \varphi^{4} p_{z}^{4} - 4} - 12 \sqrt[3]{2} \varphi^{4} p_{z}^{4} \sqrt[3]{27 \varphi^{8} p_{z}^{8} + 3 \sqrt{3} \varphi^{6} p_{z}^{6} \sqrt{27 \varphi^{4} p_{z}^{4} - 4} - 18 \varphi^{4} p_{z}^{4} + 2} - 18 \cdot 2^{\frac{2}{3}} \varphi^{4} p_{z}^{4} + 2 \left(27 \varphi^{8} p_{z}^{8} + 3 \sqrt{3} \varphi^{6} p_{z}^{6} \sqrt{27 \varphi^{4} p_{z}^{4} - 4} - 18 \varphi^{4} p_{z}^{4} + 2\right)^{\frac{2}{3}} + 2 \sqrt[3]{2} \sqrt[3]{27 \varphi^{8} p_{z}^{8} + 3 \sqrt{3} \varphi^{6} p_{z}^{6} \sqrt{27 \varphi^{4} p_{z}^{4} - 4} - 18 \varphi^{4} p_{z}^{4} + 2} + 2 \cdot 2^{\frac{2}{3}}\right)}{72 \varphi^{4} p_{z}^{5} \left(\frac{\sqrt[3]{27 \varphi^{8} p_{z}^{8} + 3 \sqrt{3} \varphi^{6} p_{z}^{6} \sqrt{27 \varphi^{4} p_{z}^{4} - 4} - 18 \varphi^{4} p_{z}^{4} + 2}}{6 \varphi^{4} p_{z}^{4} \sqrt[3]{27 \varphi^{8} p_{z}^{8} + 3 \sqrt{3} \varphi^{6} p_{z}^{6} \sqrt{27 \varphi^{4} p_{z}^{4} - 4} - 18 \varphi^{4} p_{z}^{4} + 2} + 12 \sqrt[3]{2} \varphi^{4} p_{z}^{4} - 2^{\frac{2}{3}} \left(27 \varphi^{8} p_{z}^{8} + 3 \sqrt{3} \varphi^{6} p_{z}^{6} \sqrt{27 \varphi^{4} p_{z}^{4} - 4} - 18 \varphi^{4} p_{z}^{4} + 2\right)^{\frac{2}{3}} - 2 \sqrt[3]{27 \varphi^{8} p_{z}^{8} + 3 \sqrt{3} \varphi^{6} p_{z}^{6} \sqrt{27 \varphi^{4} p_{z}^{4} - 4} - 18 \varphi^{4} p_{z}^{4} + 2} - 2 \sqrt[3]{2}}\right)^{\frac{3}{2}} \sqrt[3]{27 \varphi^{8} p_{z}^{8} + 3 \sqrt{3} \varphi^{6} p_{z}^{6} \sqrt{27 \varphi^{4} p_{z}^{4} - 4} - 18 \varphi^{4} p_{z}^{4} + 2} \left(- 6 \varphi^{4} p_{z}^{4} \sqrt[3]{27 \varphi^{8} p_{z}^{8} + 3 \sqrt{3} \varphi^{6} p_{z}^{6} \sqrt{27 \varphi^{4} p_{z}^{4} - 4} - 18 \varphi^{4} p_{z}^{4} + 2} - 12 \sqrt[3]{2} \varphi^{4} p_{z}^{4} + 2^{\frac{2}{3}} \left(27 \varphi^{8} p_{z}^{8} + 3 \sqrt{3} \varphi^{6} p_{z}^{6} \sqrt{27 \varphi^{4} p_{z}^{4} - 4} - 18 \varphi^{4} p_{z}^{4} + 2\right)^{\frac{2}{3}} + 2 \sqrt[3]{27 \varphi^{8} p_{z}^{8} + 3 \sqrt{3} \varphi^{6} p_{z}^{6} \sqrt{27 \varphi^{4} p_{z}^{4} - 4} - 18 \varphi^{4} p_{z}^{4} + 2} + 2 \sqrt[3]{2}\right)}`
        """
        # if self.eta == 2:
        #     pz_tanbeta_varphi_eqn = ( self.pz_p_beta_eqn
        #      .subs({p:self.p_varphi_beta_eqn.rhs})
        #      .subs({varphi_r:varphi})
        #      .subs({cos(beta):sqrt(1/(1+tan(beta)**2))})
        #      .subs({Abs(tan(beta)):tan(beta)})
        #     )
        #     tanbeta_pz_varphi_solns = solve( pz_tanbeta_varphi_eqn, tan(beta) )
        #     tanbeta_pz_varphi_eqn = Eq(tan(beta), ([soln for soln in tanbeta_pz_varphi_solns
        #                                         if Abs(im(sy.N(soln.subs({varphi:1,pz:1}))))<1e-20][0]) )
        #     self.fgtx_tanbeta_pz_varphi_eqn = tanbeta_pz_varphi_eqn
        #     self.fgtx_cossqrdbeta_pz_varphi_eqn = Eq(cos(beta)**2, 1/(1+tanbeta_pz_varphi_eqn.rhs**2))
        # else:
        eta_sub = {eta: self.eta}
        pz_cosbeta_varphi_tmp_eqn = ( self.pz_p_beta_eqn
         .subs({p:self.p_varphi_beta_eqn.rhs})
         .subs({varphi_r:varphi})
         .subs(eta_sub)
         .subs({Abs(tan(beta)):Abs(sin(beta))/Abs(cos(beta))})
         .subs({Abs(cos(beta)):cos(beta), Abs(sin(beta)):sin(beta)})
         .subs({sin(beta):sqrt(1-cos(beta)**2)})
        )
        pz_cosbeta_varphi_eqn = Eq( pz_cosbeta_varphi_tmp_eqn.lhs**self.eta_dbldenom,
                                    pz_cosbeta_varphi_tmp_eqn.rhs**self.eta_dbldenom )
        self.pz_cosbeta_varphi_eqn = pz_cosbeta_varphi_eqn

        self.cosbetasqrd_pz_varphi_solns = None
        self.cosbetasqrd_pz_varphi_soln = None
        self.fgtx_cossqrdbeta_pz_varphi_eqn = None
        self.fgtx_tanbeta_pz_varphi_eqn = None
        self.fgtx_px_pz_varphi_eqn = None
        self.idtx_rdotx_pz_varphi_eqn = None
        self.idtx_rdotz_pz_varphi_eqn = None
        self.cosbetasqrd_pz_varphi_solns = solve( self.pz_cosbeta_varphi_eqn, cos(beta)**2 )
        if (self.eta==Rational(1,4) or self.eta==Rational(3,2)) and self.beta_type=='tan':
            print(r'Cannot compute all indicatrix equations for $\tan\beta$ model and $\eta=$'
                        +f'{self.eta}')
            return
        def find_cosbetasqrd_root(sub):
            return [ soln for soln in self.cosbetasqrd_pz_varphi_solns
                                                     if Abs(im(sy.N(soln.subs(sub))))<1e-20
                                                     and (re(sy.N(soln.subs(sub))))>=0 ]
        self.cosbetasqrd_pz_varphi_soln = find_cosbetasqrd_root({varphi:1,pz:-0.01})
        if self.cosbetasqrd_pz_varphi_soln==[]:
            self.cosbetasqrd_pz_varphi_soln = find_cosbetasqrd_root({varphi:10,pz:-0.5})
        self.fgtx_cossqrdbeta_pz_varphi_eqn = Eq(cos(beta)**2, self.cosbetasqrd_pz_varphi_soln[0])
        self.fgtx_tanbeta_pz_varphi_eqn = Eq( tan(beta),
                                sqrt(1/(self.fgtx_cossqrdbeta_pz_varphi_eqn.rhs)-1) )
        self.fgtx_px_pz_varphi_eqn = factor( Eq(px, -pz*self.fgtx_tanbeta_pz_varphi_eqn.rhs ) )
        g_xx = self.gstar_varphi_pxpz_eqn.rhs[0,0]
        g_zx = self.gstar_varphi_pxpz_eqn.rhs[1,0]
        g_xz = self.gstar_varphi_pxpz_eqn.rhs[0,1]
        g_zz = self.gstar_varphi_pxpz_eqn.rhs[1,1]
        self.idtx_rdotx_pz_varphi_eqn = factor(
            Eq(rx, (g_xx*px+g_xz*pz).subs({px:self.fgtx_px_pz_varphi_eqn.rhs,varphi_r:varphi})) )
        self.idtx_rdotz_pz_varphi_eqn = factor(factor(
            Eq(rz, (g_zx*px+g_zz*pz).subs({px:self.fgtx_px_pz_varphi_eqn.rhs,varphi_r:varphi})) ))


    def prep_geodesic_eqns(self, parameters=None):
        r"""
        Define geodesic equations

        Args:
            parameters (dict): dictionary of model parameter values to be used for equation substitutions

        Attributes:
            gstar_ij_tanbeta_mat   (:class:`sympy.ImmutableDenseMatrix <sympy.matrices.immutable.ImmutableDenseMatrix>`) :
                :math:`\dots`
            g_ij_tanbeta_mat   (:class:`sympy.ImmutableDenseMatrix <sympy.matrices.immutable.ImmutableDenseMatrix>`) :
                :math:`\dots`
            tanbeta_poly_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`\dots` where :math:`a := \tan\alpha`
            tanbeta_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`\tan{\left(\beta \right)} = \dots` where :math:`a := \tan\alpha`
            gstar_ij_tanalpha_mat   (:class:`sympy.ImmutableDenseMatrix <sympy.matrices.immutable.ImmutableDenseMatrix>`) :
                a symmetric tensor with components (using shorthand :math:`a := \tan\alpha`)

                :math:`g^*[1,1] = \dots`

                :math:`g^*[1,2] = g^*[2,1] = \dots`

                :math:`g^*[2,2] = \dots`
            gstar_ij_mat   (:class:`sympy.ImmutableDenseMatrix <sympy.matrices.immutable.ImmutableDenseMatrix>`) :
                a symmetric tensor with components
                (using shorthand :math:`a := \tan\alpha`, and with a particular choice of model parameters)

                :math:`g^*[1,1] = \dots`

                :math:`g^*[1,2] = g^*[2,1] = \dots`

                :math:`g^*[2,2] =  \dots`
            g_ij_tanalpha_mat   (:class:`sympy.ImmutableDenseMatrix <sympy.matrices.immutable.ImmutableDenseMatrix>`) :
                a symmetric tensor with components (using shorthand :math:`a := \tan\alpha`)

                :math:`g[1,1] = \dots`

                :math:`g[1,2] = g[2,1] = \dots`

                :math:`g[2,2] = \dots`
            g_ij_mat   (:class:`sympy.ImmutableDenseMatrix <sympy.matrices.immutable.ImmutableDenseMatrix>`) :
                a symmetric tensor with components
                (using shorthand :math:`a := \tan\alpha`, and with a particular choice of model parameters)

                :math:`g[1,1] =\dots`

                :math:`g[1,2] = g[2,1] = \dots`

                :math:`g[2,2] = \dots`
            g_ij_mat_lambdified   (function) :
                lambdified version of `g_ij_mat`
            gstar_ij_mat_lambdified   (function) :
                lambdified version of `gstar_ij_mat`
        """
        self.gstar_ij_tanbeta_mat = None
        self.g_ij_tanbeta_mat = None
        self.tanbeta_poly_eqn = None
        self.tanbeta_eqn = None
        self.gstar_ij_tanalpha_mat = None
        self.gstar_ij_mat = None
        self.g_ij_tanalpha_mat = None
        self.g_ij_mat = None
        self.g_ij_mat_lambdified = None
        self.gstar_ij_mat_lambdified = None

        if self.eta>=1 and self.beta_type=='sin':
            print(r'Cannot compute geodesic equations for $\sin\beta$ model and $\eta>=1$')
            return
        mu_eta_sub = {mu: self.mu, eta: self.eta}

        # if parameters is None: return
        H_ = self.H_eqn.rhs.subs(mu_eta_sub)
        # Assume indexing here ranges in [1,2]
        p_i_lambda = lambda i: [px, pz][i-1]
        r_i_lambda = lambda i: [rx, rz][i-1]
        rdot_i_lambda = lambda i: [rdotx, rdotz][i-1]
        gstar_ij_lambda = lambda i,j: simplify( Rational(2,2)*diff(diff(H_,p_i_lambda(i)),p_i_lambda(j)) )
        gstar_ij_mat = Matrix([[gstar_ij_lambda(1,1),gstar_ij_lambda(2,1)],
                               [gstar_ij_lambda(1,2),gstar_ij_lambda(2,2)]])
        gstar_ij_pxpz_mat = gstar_ij_mat.subs({varphi_r:varphi_rx})
        g_ij_pxpz_mat = gstar_ij_mat.inv().subs({varphi_r:varphi_rx})

        # FIX THIS
        self.gstar_ij_tanbeta_mat = simplify( gstar_ij_pxpz_mat.subs(e2d(self.px_pz_tanbeta_eqn)) )
        self.g_ij_tanbeta_mat = simplify( g_ij_pxpz_mat.subs(e2d(self.px_pz_tanbeta_eqn)) )

        # HACK!!!   These choices of solutions should not be hardwired but should be dependent
        #           on a search for the real, non-zero solution

        # tb_poly_eqn = Eq(tb**3*sy.poly(
        #     self.tanalpha_beta_eqn.subs({tan(alpha):ta, tan(beta):-tb}), tb**3).as_expr())
        # #TODO: replace with more generic solutions to be defined above
        # # tanbeta_eqn = self.tanbeta_alpha_eqn.subs({tan(alpha):ta})
        # self.tb_tmp1 = solve(tb_poly_eqn, tb)
        # self.tb_tmp2 = solve(tb_poly_eqn, tb**2)
        # tanbeta_eqn = Eq(tan(beta),simplify( solve(tb_poly_eqn, tb)[0] ))
        # tan2beta_eqn = Eq(tan(beta)**2,simplify( solve(tb_poly_eqn, tb**2)[1] ))

        tanalpha_beta_eqn = self.tanalpha_beta_eqn.subs(mu_eta_sub)
        tanbeta_poly_eqn = Eq(
            sy.numer(tanalpha_beta_eqn.rhs) - tanalpha_beta_eqn.lhs*sy.denom(tanalpha_beta_eqn.rhs), 0) \
                                        .subs({tan(alpha):ta})

        # HACK!!!  which of the (?) two roots should be chosen?
        tanbeta_eqn  = (Eq(tan(beta), solve(tanbeta_poly_eqn, tan(beta))[0]))
        self.tanbeta_poly_eqn = tanbeta_poly_eqn
        self.tanbeta_eqn = tanbeta_eqn
        cosbeta_eqn = Eq(cos(beta), 1/sqrt(1+tan(beta)**2))
        sinbeta_eqn = Eq(sin(beta), sqrt(1-1/(1+tan(beta)**2)))
        sintwobeta_eqn = Eq(sin(2*beta), cos(beta)**2-sin(beta)**2)

        # Replace all refs to beta with refs to alpha
        self.gstar_ij_tanalpha_mat = ( self.gstar_ij_tanbeta_mat
                                        .subs(e2d(sintwobeta_eqn))
                                        .subs(e2d(sinbeta_eqn))
                                        .subs(e2d(cosbeta_eqn))
                                        .subs(e2d(tanbeta_eqn))
                                        ).subs(mu_eta_sub)
        # Use tan(alpha) equation instead of hardwired sub here
        self.gstar_ij_mat = ( self.gstar_ij_tanalpha_mat
                                        .subs({ta:rdotz/rdotx})
                                        .subs(e2d(self.varphi_rx_eqn.subs({varphi_r:varphi_rx})))
                                        .subs(parameters) ).subs(mu_eta_sub)
        self.g_ij_tanalpha_mat = ( self.g_ij_tanbeta_mat
                                        .subs(e2d(sintwobeta_eqn))
                                        .subs(e2d(sinbeta_eqn))
                                        .subs(e2d(cosbeta_eqn))
                                        .subs(e2d(tanbeta_eqn))
                                        ).subs(mu_eta_sub)
        self.g_ij_mat = ( self.g_ij_tanalpha_mat
                                        .subs({ta:rdotz/rdotx})
                                        .subs(e2d(self.varphi_rx_eqn.subs({varphi_r:varphi_rx})))
                                        .subs(parameters) ).subs(mu_eta_sub)
        # return self.g_ij_mat
        self.g_ij_mat_lambdified = lambdify( (rx,rdotx,rdotz, varepsilon), self.g_ij_mat, 'numpy')
        self.gstar_ij_mat_lambdified = lambdify( (rx,rdotx,rdotz, varepsilon), self.gstar_ij_mat, 'numpy')


    def define_geodesic_eqns(self, parameters=None):
        r"""
        Define geodesic equations

        Args:
            parameters (dict): dictionary of model parameter values to be used for equation substitutions

        Attributes:
            dg_rk_ij_mat   (:class:`sympy.ImmutableDenseMatrix <sympy.matrices.immutable.ImmutableDenseMatrix>`) :
                Derivatives of the components of the metric tensor:
                these values are used to construct the Christoffel tensor.
                Too unwieldy to display here.
            christoffel_ij_k_rx_rdot_lambda   (function) :
                The Christoffel tensor coefficients, as a `lambda` function,
                for each component :math:`r^x`, :math:`{\dot{r}^x}` and :math:`{\dot{r}^z}`.
            christoffel_ij_k_lambda   (function) :
                The Christoffel tensor coefficients, as a `lambda` function, in a compact and indexable form.
            geodesic_eqns (list of :class:`sympy.Eq <sympy.core.relational.Equality>`) :
                Ray geodesic equations, but expressed indirectly as a pair of coupled 1st-order vector ODEs
                rather than a 2nd-order vector ODE for ray acceleration.
                The 1st-order ODE form is easier to solve numerically.

                :math:`\dot{r}^x = v^{x}`

                :math:`\dot{r}^z = v^{z}`

                :math:`\dot{v}^x = \dots`

                :math:`\dot{v}^z = \dots`
            vdotx_lambdified   (function) :
                lambdified version of :math:`\dot{v}^x`
            vdotz_lambdified   (function) :
                lambdified version of :math:`\dot{v}^z`
        """
        self.dg_rk_ij_mat = None
        self.christoffel_ij_k_rx_rdot_lambda = None
        self.christoffel_ij_k_lambda = None
        self.geodesic_eqns = None
        self.vdotx_lambdified = None
        self.vdotz_lambdified = None
        if self.eta>=1 and self.beta_type=='sin':
            print(r'Cannot compute geodesic equations for $\sin\beta$ model and $\eta>=1$')
            return
        eta_sub = {eta: self.eta}

        # Manipulate metric tensors
        gstar_ij_lambda = lambda i_,j_: self.gstar_ij_mat[i_,j_]
        g_ij_lambda = lambda i_,j_: self.g_ij_mat[i_,j_]
        r_k_mat = Matrix([rx, rz])
        self.dg_rk_ij_mat = (derive_by_array(self.g_ij_mat,r_k_mat))
        dg_ij_rk_lambda = lambda i_,j_,k_: self.dg_rk_ij_mat[k_,0,i_,j_]

        # Generate Christoffel "symbols" tensor
        christoffel_ij_k_raw = lambda i_,j_,k_: [
                                        Rational(1,2)*gstar_ij_lambda(k_,m_)*(
                                          dg_ij_rk_lambda(m_,i_,j_)
                                        + dg_ij_rk_lambda(m_,j_,i_)
                                        - dg_ij_rk_lambda(i_,j_,m_))
                                    for m_ in [0,1] ]
        # Use of 'factor' here messes things up for eta<1
        self.christoffel_ij_k_rx_rdot_lambda = lambda i_,j_,k_: \
            (reduce(lambda a,b: a+b, christoffel_ij_k_raw(i_,j_,k_)))
        christoffel_ij_k_rx_rdot_list = [[[
            lambdify( (rx, rdotx, rdotz, varepsilon), self.christoffel_ij_k_rx_rdot_lambda(i_,j_,k_) )
                                               for i_ in [0,1]]
                                              for j_ in [0,1]]
                                             for k_ in [0,1]]
        self.christoffel_ij_k_lambda = lambda i_,j_,k_, varepsilon_: christoffel_ij_k_rx_rdot_list[i_][j_][k_]

        # Obtain geodesic equations as a set of coupled 1st order ODEs
        self.geodesic_eqns = Matrix([
            Eq(rdotx_true, rdotx),
            Eq(rdotz_true, rdotz),
            # Use symmetry to abbreviate sum of diagonal terms
            Eq(vdotx, (-self.christoffel_ij_k_rx_rdot_lambda(0,0,0)*rdotx*rdotx
                       -2*self.christoffel_ij_k_rx_rdot_lambda(0,1,0)*rdotx*rdotz
                       #-christoffel_ij_k_rx_rdot_lambda(1,0,0)*rdotz*rdotx
                       -self.christoffel_ij_k_rx_rdot_lambda(1,1,0)*rdotz*rdotz) ),
            # Use symmetry to abbreviate sum of diagonal terms
            Eq(vdotz, (-self.christoffel_ij_k_rx_rdot_lambda(0,0,1)*rdotx*rdotx
                       -2*self.christoffel_ij_k_rx_rdot_lambda(0,1,1)*rdotx*rdotz
                       #-christoffel_ij_k_rx_rdot_lambda(1,0,1)*rdotz*rdotx
                       -self.christoffel_ij_k_rx_rdot_lambda(1,1,1)*rdotz*rdotz) )
        ])
        # Use of 'factor' here messes things up for eta<1
        self.vdotx_lambdified = sy.lambdify( (rx, rdotx,rdotz, varepsilon), (self.geodesic_eqns[2].rhs), 'numpy')
        self.vdotz_lambdified = sy.lambdify( (rx, rdotx,rdotz, varepsilon), (self.geodesic_eqns[3].rhs), 'numpy')


    def define_px_poly_eqn(self, eta_choice=None):
        r"""
        Define polynomial form of function combining normal-slowness covector components :math:`(p_x,p_z)`
        (where the latter is given in terms of the vertical erosion rate :math:`\xi^{\downarrow} = -\dfrac{1}{p_z}`)
        and the erosion model flow component :math:`\varphi(\mathbf{r})`


        Args:
            eta_choice (:class:`sympy.Rational <sympy.core.numbers.Rational>`):
                value of :math:`\eta` to use instead value given at instantiation; otherwise the latter value is used

        Attributes:
            poly_px_xiv_varphi_eqn   (:class:`sympy.Poly <sympy.polys.polytools.Poly>`) :
                :math:`\operatorname{Poly}{\left( \left(\xi^{\downarrow}\right)^{4} \varphi^{4}{\left(\mathbf{r} \right)} p_{x}^{6}
                -  \left(\xi^{\downarrow}\right)^{4} p_{x}^{2} -  \left(\xi^{\downarrow}\right)^{2}, p_{x},
                domain=\mathbb{Z}\left[\varphi{\left(\mathbf{r} \right)}, \xi^{\downarrow}\right] \right)}`
            poly_px_xiv0_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`\varphi_0^{4} \left(\xi^{\downarrow{0}}\right)^{4} p_{x}^{6} \left(\varepsilon
                + \left(\frac{x_{1} - {r}^x}{x_{1}}\right)^{2 \mu}\right)^{4}
                - \left(\xi^{\downarrow{0}}\right)^{4} p_{x}^{2}
                - \left(\xi^{\downarrow{0}}\right)^{2} = 0`
        """
        if eta_choice is None:
            eta_ = self.eta
        else:
            eta_ = eta_choice
        tmp_eqn = simplify(self.px_xiv_varphi_eqn.subs({eta:eta_}))
        if eta_<=1:
            self.poly_px_xiv_varphi_eqn = poly( tmp_eqn.lhs, px)
        else:
            self.poly_px_xiv_varphi_eqn = poly(numer(tmp_eqn.lhs), px)
        self.poly_px_xiv0_eqn = Eq(self.poly_px_xiv_varphi_eqn.subs(e2d(self.varphi_rx_eqn)) \
                                                              .subs({xiv:xiv_0}), 0)


    def prep_ibc_eqns(self):
        r"""
        Define boundary (ray initial) condition equations

        Attributes:
            pz0_xiv0_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`p_{z_0} = - \dfrac{1}{\xi^{\downarrow{0}}}`
            pzpx_unity_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`\varphi^{2} p_{x}^{2} p_{x}^{2 \eta} \left(p_{x}^{2} + p_{z}^{2}\right)^{- \eta} + \varphi^{2} p_{x}^{2 \eta} p_{z}^{2} \left(p_{x}^{2} + p_{z}^{2}\right)^{- \eta} = 1`
        """
        self.pz0_xiv0_eqn = pz0_xiv0_eqn = Eq(pz_0, (-1/xiv_0)) # changed sign
        self.pzpx_unity_eqn = expand(simplify(
            self.rdot_p_unity_eqn.subs({rdotx:self.rdotx_pxpz_eqn.rhs,
                            rdotz:self.rdotz_pxpz_eqn.rhs}).subs({varphi_r:varphi}) )).subs({Abs(pz):-pz})


    def define_ibc_eqns(self):
        r"""
        Define initial profile equations

        Attributes:
            boundary_eqns   (`dict` of :class:`sympy.Eq <sympy.core.relational.Equality>`) :

                'planar':
                    'h': :math:`h = \dfrac{h_{0} x}{x_{1}}`

                    'gradh': :math:`\dfrac{d}{d x} h{\left(x \right)} = \dfrac{h_{0}}{x_{1}}`

                'convex-up':
                    'h': :math:`h = \dfrac{h_{0} \tanh{\left(\dfrac{\kappa_\mathrm{h} x}{x_{1}} \right)}}{\tanh{\left(\dfrac{\kappa_\mathrm{h}}{x_{1}} \right)}}`

                    'gradh': :math:`\dfrac{d}{d x} h{\left(x \right)} = \dfrac{\kappa_\mathrm{h} h_{0} \left(1 - \tanh^{2}{\left(\dfrac{\kappa_\mathrm{h} x}{x_{1}} \right)}\right)}{x_{1} \tanh{\left(\dfrac{\kappa_\mathrm{h}}{x_{1}} \right)}}`

                'concave-up':
                    'h': :math:`h = h_{0} \left(1 + \dfrac{\tanh{\left(\dfrac{\kappa_\mathrm{h} x}{x_{1}} - \kappa_\mathrm{h} \right)}}{\tanh{\left(\dfrac{\kappa_\mathrm{h}}{x_{1}} \right)}}\right)`

                    'gradh': :math:`\dfrac{d}{d x} h{\left(x \right)} = \dfrac{\kappa_\mathrm{h} h_{0} \left(1 - \tanh^{2}{\left(\dfrac{\kappa_\mathrm{h} x}{x_{1}} - \kappa_\mathrm{h} \right)}\right)}{x_{1} \tanh{\left(\dfrac{\kappa_\mathrm{h}}{x_{1}} \right)}}`
        """
        self.boundary_eqns = {
            'planar' : {'h': Eq(h, (h_0*x/x_1))},
            'convex-up' : {'h': simplify(Eq(h, h_0*sy.tanh(kappa_h*x/x_1)/sy.tanh(kappa_h/x_1)))},
            'concave-up' : {'h': simplify(Eq(h, h_0+h_0*sy.tanh(-kappa_h*(x_1-x)/x_1)/sy.tanh(kappa_h/x_1)))}
        }
        # Math concave-up not geo concave-up, i.e., with minimum
        # Math convex-up not geo convex-up, i.e., with maximum
        for ibc_type in ['planar','convex-up','concave-up']:
            self.boundary_eqns[ibc_type].update({
                'gradh': Eq(diff(h_fn,x),diff(self.boundary_eqns[ibc_type]['h'].rhs,x))
                })


    def set_ibc_eqns(self):
        r"""
        Define initial condition equations

        Attributes:
            rz_initial_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`{r}^z = \dfrac{h_{0} \tanh{\left(\frac{\kappa_\mathrm{h} {r}^x}{x_{1}} \right)}}{\tanh{\left(\frac{\kappa_\mathrm{h}}{x_{1}} \right)}}`
            tanbeta_initial_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`\tan{\left(\beta \right)} = \dfrac{\kappa_\mathrm{h} h_{0} \left(1 - \tanh^{2}{\left(\frac{\kappa_\mathrm{h} x}{x_{1}} \right)}\right)}{x_{1} \tanh{\left(\frac{\kappa_\mathrm{h}}{x_{1}} \right)}}`
            p_initial_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`p = \dfrac{x_{1}^{2 \mu} \left|{\sin{\left(\beta \right)}}\right|^{- \eta}}{\varphi_0 \left(\varepsilon x_{1}^{2 \mu} + \left(- x + x_{1}\right)^{2 \mu}\right)}`
            px_initial_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`p_{x} = \dfrac{\kappa_\mathrm{h} h_{0} x_{1}^{2 \mu} \left(\dfrac{1}{\kappa_\mathrm{h} h_{0} \left|{\tanh^{2}{\left(\frac{\kappa_\mathrm{h} x}{x_{1}} \right)} - 1}\right|}\right)^{\eta} \left(\kappa_\mathrm{h}^{2} h_{0}^{2} \left(\tanh^{2}{\left(\frac{\kappa_\mathrm{h} x}{x_{1}} \right)} - 1\right)^{2} + x_{1}^{2} \tanh^{2}{\left(\frac{\kappa_\mathrm{h}}{x_{1}} \right)}\right)^{\frac{\eta}{2} - \frac{1}{2}} \left|{\tanh^{2}{\left(\frac{\kappa_\mathrm{h} x}{x_{1}} \right)} - 1}\right|}{\varphi_0 \left(\varepsilon x_{1}^{2 \mu} + \left(- x + x_{1}\right)^{2 \mu}\right)}`
            pz_initial_eqn   (:class:`sympy.Eq <sympy.core.relational.Equality>`) :
                :math:`p_{z} = - \dfrac{x_{1}^{2 \mu + 1} \left(\dfrac{1}{\kappa_\mathrm{h} h_{0} \left|{\tanh^{2}{\left(\frac{\kappa_\mathrm{h} x}{x_{1}} \right)} - 1}\right|}\right)^{\eta} \left(\kappa_\mathrm{h}^{2} h_{0}^{2} \left(\tanh^{2}{\left(\frac{\kappa_\mathrm{h} x}{x_{1}} \right)} - 1\right)^{2} + x_{1}^{2} \tanh^{2}{\left(\frac{\kappa_\mathrm{h}}{x_{1}} \right)}\right)^{\frac{\eta}{2} - \frac{1}{2}} \tanh{\left(\frac{\kappa_\mathrm{h}}{x_{1}} \right)}}{\varphi_0 \left(\varepsilon x_{1}^{2 \mu} + \left(- x + x_{1}\right)^{2 \mu}\right)}`
        """
        cosbeta_eqn = Eq(cos(beta), 1/sqrt(1+tan(beta)**2))
        sinbeta_eqn = Eq(sin(beta), sqrt(1-1/(1+tan(beta)**2)))
        sintwobeta_eqn = Eq(sin(2*beta), cos(beta)**2-sin(beta)**2)

        ibc_type = self.ibc_type
        self.rz_initial_eqn = self.boundary_eqns[ibc_type]['h'].subs({h:rz, x:rx})
        self.tanbeta_initial_eqn = Eq(tan(beta), self.boundary_eqns[ibc_type]['gradh'].rhs)
        self.p_initial_eqn = simplify( self.p_varphi_beta_eqn
                                  .subs(e2d(self.varphi_rx_eqn))
                                  # .subs({varphi_r:self.varphi_rx_eqn.rhs})
                                  .subs({self.tanbeta_initial_eqn.lhs: self.tanbeta_initial_eqn.rhs})
                                  .subs({rx:x}) )
        self.px_initial_eqn = Eq(px, simplify(
            (+self.p_initial_eqn.rhs*sin(beta))
            .subs(e2d(sinbeta_eqn))
            .subs(e2d(cosbeta_eqn))
            .subs({tan(beta):self.tanbeta_initial_eqn.rhs, rx:x})) )
        self.pz_initial_eqn = Eq(pz, simplify(
            (-self.p_initial_eqn.rhs*cos(beta))
            .subs(e2d(sinbeta_eqn))
            .subs(e2d(cosbeta_eqn))
            .subs({tan(beta):self.tanbeta_initial_eqn.rhs, rx:x})) )
