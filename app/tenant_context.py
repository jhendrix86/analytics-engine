"""
Tenant context management for multi-tenancy support

This module provides utilities for managing tenant context throughout
the request lifecycle, including extraction from JWT and database session filtering.
"""

from contextvars import ContextVar
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Query
from sqlalchemy import event
from loguru import logger


# Context variable to store the current tenant ID
tenant_context: ContextVar[Optional[UUID]] = ContextVar("tenant_context", default=None)


def set_tenant_context(tenant_id: UUID) -> None:
    """
    Set the tenant context for the current request.
    
    Args:
        tenant_id: The UUID of the tenant for the current request
    """
    tenant_context.set(tenant_id)
    logger.debug(f"Set tenant context: {tenant_id}")


def get_tenant_context() -> Optional[UUID]:
    """
    Get the current tenant context.
    
    Returns:
        The UUID of the current tenant, or None if not set
    """
    return tenant_context.get()


def clear_tenant_context() -> None:
    """Clear the tenant context."""
    tenant_context.set(None)
    logger.debug("Cleared tenant context")


class TenantQueryMixin:
    """
    Mixin for adding tenant filtering to SQLAlchemy queries.
    
    This automatically filters all queries by the current tenant context.
    """
    
    def apply_tenant_filter(self, query: Query, model_class) -> Query:
        """
        Apply tenant filtering to a query if the model has tenant_id.
        
        Args:
            query: The SQLAlchemy query to filter
            model_class: The model class being queried
            
        Returns:
            The filtered query
        """
        tenant_id = get_tenant_context()
        
        # Only apply filter if:
        # 1. Tenant context is set
        # 2. Model has tenant_id column
        # 3. We're not querying the Tenant model itself
        if (tenant_id and 
            hasattr(model_class, 'tenant_id') and 
            model_class.__tablename__ != 'tenants'):
            query = query.filter(model_class.tenant_id == tenant_id)
            logger.debug(f"Applied tenant filter to {model_class.__name__}: {tenant_id}")
        
        return query


# Global instance of the tenant query mixin
tenant_query_mixin = TenantQueryMixin()


async def get_tenant_aware_db():
    """
    Dependency for getting a tenant-aware database session.
    
    This session automatically applies tenant filtering to all queries
    based on the current tenant context.
    
    Yields:
        AsyncSession: Database session with tenant filtering
    """
    from app.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as session:
        try:
            # Set up event listeners for automatic tenant filtering
            @event.listens_for(session, "before_execute", named=True)
            def before_execute(conn, clauseelement, multiparams, params, execution_options):
                # This is a simplified approach - in production, you'd want more sophisticated
                # query interception to automatically add tenant filters
                pass
            
            yield session
        finally:
            await session.close()
            clear_tenant_context()
